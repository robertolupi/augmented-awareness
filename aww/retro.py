import asyncio
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Sequence
import hashlib

from pydantic_ai import Agent
from pydantic_ai.models import Model

import yaml

from aww.obsidian import Vault, Page, Level, Node, Tree, build_retrospective_tree


def md5(s: str) -> str:
    """Return the MD5 hash of the given string."""
    return hashlib.md5(s.encode("utf-8")).hexdigest()


MARKDOWN_RE = re.compile('```markdown\n(.*?)\n```', re.DOTALL | re.MULTILINE)


@dataclass
class RetrospectiveResult:
    """Holds the result of a retrospective generation, including dates, output, and the associated page."""
    dates: list[date]
    output: str
    page: Page


import logging

logger = logging.getLogger(__name__)

CachePolicy = Callable[[Node, Tree], None]
"""Type alias for cache policy functions that operate on a Node and Tree."""


class NoRootCachePolicy(CachePolicy):
    """Cache policy that disables cache for the root node."""
    def __call__(self, node: Node, tree: Tree):
        """Disable cache for the given node (root)."""
        node.use_cache = False


class NoLevelsCachePolicy(CachePolicy):
    """Cache policy that disables cache for nodes at specified levels."""
    def __init__(self, levels: Sequence[Level]):
        """Initialize with a sequence of levels for which cache should be disabled."""
        self.levels = set(levels)

    def __call__(self, node: Node, tree: Tree):
        """Disable cache for sources of the node if their level is in the specified levels."""
        for source in node.sources:
            if source.level in self.levels:
                source.use_cache = False


class ModificationTimeCachePolicy(CachePolicy):
    """Cache policy that disables cache if the source page is newer than the retro page."""
    def __call__(self, node: Node, tree: Tree):
        """Disable cache for nodes where the source page modification time is newer than the retro page."""
        for n in tree.values():
            if not n.page or not n.retro_page:
                continue
            if n.page.mtime_ns() > n.retro_page.mtime_ns():
                n.use_cache = False


class TooOldCachePolicy(CachePolicy):
    """Cache policy that disables cache for retro pages older than a given datetime limit."""
    def __init__(self, limit: datetime):
        """Initialize with a datetime limit; retro pages older than this will not use cache."""
        self.limit = limit

    def __call__(self, node: Node, tree: Tree):
        """Disable cache for nodes whose retro page modification time is older than the limit."""
        limit_ns = self.limit.timestamp() * 1e9
        for n in tree.values():
            if not n.retro_page:
                continue
            if n.retro_page.mtime_ns() < limit_ns:
                n.use_cache = False


# Table-driven approach for extensible frontmatter metrics
METRIC_FORMATTERS = {
    # Table-driven approach for extensible frontmatter metrics
    'stress': 'Stress level {} of 10.',
    'kg': 'Weight {} kg.',
    'bmi': 'Body Mass Index (BMI) {}.',
    'mood': 'Mood: {}',
    'meditation': 'Meditation: {}',
    'relax': 'Relax: {}',
    'career': 'Career: {}',
    'social': 'Social connections: {}',
    'exercise': 'Exercise: {}',
    'sleep_score': "Sleep Score: {} of 100.",
    'vitals_score': "Vitals Score: {} of 100.",
    'activity_score': "Activity Score: {} of 100.",
    'relax_score': "Relax Score: {} of 100.",
}


async def page_content(node):
    """Return the content of a node's page, including formatted frontmatter metrics if present."""
    content = [f'Page: [[{node.page.name}]]', node.page.content()]
    if fm := node.page.frontmatter():
        for key, fmt in METRIC_FORMATTERS.items():
            if (value := fm.get(key)) is not None:
                content.append(fmt.format(value))
    return '\n'.join(content)


async def prepare_output(node, result):
    """Prepare the output for a retrospective, extracting markdown and formatting the title."""
    output = result.output.strip()
    if m := MARKDOWN_RE.match(output):
        output = m.group(1)
    output = output.replace('![[', '[[')
    output_title = f"# {node.retro_page.name}"
    output = output_title + "\n\n" + output
    return output


class RecursiveRetrospectiveGenerator:
    """
    Generates retrospectives recursively for a set of dates and a given level using an AI agent.
    Handles cache policies, concurrency, and prompt management.
    """
    def __init__(self, model: Model, vault: Vault, dates: list[date], level: Level, concurrency_limit: int = 10,
                 prompts_path: Path | None = None):
        """
        Initialize the generator with model, vault, dates, level, concurrency limit, and optional prompts path.
        Loads system prompts and sets up agents for each level.
        """
        if not prompts_path:
            prompts_path = (Path(__file__).parent / 'retro')

        self.prompts = {l: (prompts_path / f"{l.name}.md").read_text() for l in Level}
        self.agents = {l: Agent(model=model, system_prompt=self.prompts[l]) for l in Level}
        self.vault = vault
        self.tree = build_retrospective_tree(vault, dates)
        self.dates = dates
        self.max_level = level
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def run(self, context_levels: list[Level],
                  cache_policies: list[CachePolicy],
                  gather=asyncio.gather) -> RetrospectiveResult | None:
        """
        Run the retrospective generation for the configured dates and level.
        Applies cache policies and generates the result for the root node.
        """
        retro_page = self.vault.retrospective_page(self.dates[0], self.max_level)
        node = self.tree[retro_page]
        for policy in cache_policies:
            policy(node, self.tree)
        return await self._generate(node, set(context_levels), gather)

    async def _generate(self, node: Node, context_levels: set[Level],
                        gather=asyncio.gather) -> RetrospectiveResult | None:
        """
        Recursively generate retrospectives for the given node and its sources.
        Returns a RetrospectiveResult or None if no content is available.
        """
        if node.use_cache and node.retro_page:
            return RetrospectiveResult(dates=list(node.dates), output=node.retro_page.content(), page=node.retro_page)

        sources = list(sorted(node.sources))

        source_results = await gather(
            *[self._generate(source, context_levels) for source in sources if source.level in context_levels])

        source_content = [result.output for result in source_results if result]
        if node.page:
            source_content.insert(0, await page_content(node))
        if not source_content:
            return None

        agent = self.agents[node.level]
        model_name = agent.model.model_name
        sys_prompt = self.prompts[node.level]

        async with self.semaphore:
            result = await agent.run(user_prompt=source_content)

        usage = result.usage()
        retro_frontmatter = dict(
            sys_prompt_hash=md5(sys_prompt),
            model_name=model_name,
            ctime=datetime.now().isoformat(),
            user_prompt_hash=md5('\n'.join(source_content)),
            request_tokens=usage.request_tokens,
            response_tokens=usage.response_tokens,
            total_tokens=usage.total_tokens,
            details=usage.details,
            requests=usage.requests,
        )

        output = await prepare_output(node, result)
        await self.save_retro_page(node, output, sources, context_levels, retro_frontmatter)
        return RetrospectiveResult(dates=list(node.dates), output=output, page=node.retro_page)

    @staticmethod
    async def save_retro_page(node, output, sources, levels, retro_frontmatter):
        """
        Save the generated retrospective page to disk, including frontmatter and source references.
        """
        # ensure parent directory exists
        node.retro_page.path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(
            "Writing retrospective page %s (level=%s)",
            node.retro_page.path,
            node.level,
        )
        with node.retro_page.path.open('w') as fd:
            source_items = []
            if node.page:
                source_items.append(f"[[{node.page.name}]]")
            for n in sources:
                if not n.retro_page:
                    continue
                if n.level in levels:
                    source_items.append(f"[[{n.retro_page.name}]]")

            retro_frontmatter['sources'] = source_items
            fd.write("---\n")
            fd.write(yaml.dump(retro_frontmatter, default_flow_style=False))
            fd.write("---\n")
            fd.write(output)
