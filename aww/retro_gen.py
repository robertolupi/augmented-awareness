import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime

import yaml
from pydantic_ai import Agent
from pydantic_ai.models import Model

from aww.config import Settings
from aww.obsidian import Level, Page
from aww.prompts import get_prompt_template
from aww.retro import CachePolicy, Node, Selection


def md5(s: str) -> str:
    """Return the MD5 hash of the given string."""
    return hashlib.md5(s.encode("utf-8")).hexdigest()


MARKDOWN_RE = re.compile("```markdown\n(.*?)\n```", re.DOTALL | re.MULTILINE)


@dataclass
class RecursiveResult:
    """Holds the result of a recursive generation, including dates, output, and the associated page."""

    dates: list[date]
    output: str
    page: Page


logger = logging.getLogger(__name__)

# Table-driven approach for extensible frontmatter metrics
METRIC_FORMATTERS = {
    # Table-driven approach for extensible frontmatter metrics
    "stress": "Stress level {} of 10.",
    "kg": "Weight {} kg.",
    "bmi": "Body Mass Index (BMI) {}.",
    "mood": "Mood: {}",
    "meditation": "Meditation: {}",
    "relax": "Relax: {}",
    "career": "Career: {}",
    "social": "Social connections: {}",
    "exercise": "Exercise: {}",
    "sleep_score": "Sleep Score: {} of 100.",
    "vitals_score": "Vitals Score: {} of 100.",
    "activity_score": "Physical Activity Score: {} of 100.",
    "relax_score": "Relax Score: {} of 100.",
    "pushups": "Push-ups: {}",
    "exercise_time": "Exercise Time: {} minutes",
}


async def page_content(node) -> str:
    """Return the content of a node's page, including formatted frontmatter metrics if present."""
    content = [f"Page: [[{node.page.name}]]", node.page.content()]
    if fm := node.page.frontmatter():
        for key, fmt in METRIC_FORMATTERS.items():
            if (value := fm.get(key)) is not None:
                content.append(fmt.format(value))
    return "\n".join(content)


async def prepare_output(node, result, target_page) -> str:
    """Prepare the output for a recursive generation, extracting markdown and formatting the title."""
    output = result.output.strip()
    if m := MARKDOWN_RE.match(output):
        output = m.group(1)
    output = output.replace("![[", "[[")
    output_title = f"# {target_page.name}"
    output = output_title + "\n\n" + output
    return output


class RecursiveGenerator:
    """
    Generates content recursively for a set of dates and a given level using an AI agent.
    Handles cache policies, concurrency, and prompt management.
    """

    def __init__(
        self,
        model: Model,
        sel: Selection,
        concurrency_limit: int = 10,
        prompt_prefix: str = "",
        extra_vars: dict = None,
        get_target_page=None,
    ):
        """
        Initialize the generator with model, selection, and other parameters.
        Loads system prompts and sets up agents for each level.
        """
        self.extra_vars = extra_vars or {}
        self.prompt_prefix = prompt_prefix
        # Default target page is the retro_page from the node
        self.get_target_page = get_target_page or (lambda node: node.retro_page)

        settings = Settings()
        normalized_tags = {}
        for tag, desc in (settings.tags or {}).items():
            normalized_tag = tag.strip().lower().replace(" ", "_")
            if not normalized_tag:
                continue
            normalized_tags[normalized_tag] = (desc or "").strip()

        canonical_tags = sorted(normalized_tags.keys())
        canonical_tags_block_lines = []
        for tag in canonical_tags:
            desc = normalized_tags[tag]
            if desc:
                canonical_tags_block_lines.append(f"- #{tag}: {desc}")
            else:
                canonical_tags_block_lines.append(f"- #{tag}")
        canonical_tags_block = "\n".join(canonical_tags_block_lines)

        self.prompts = {
            l: get_prompt_template(f"{self.prompt_prefix}{l.name}.md").render(
                canonical_tags=canonical_tags,
                canonical_tags_block=canonical_tags_block,
                **self.extra_vars,
            )
            for l in Level
        }
        self.agents = {
            l: Agent(model=model, system_prompt=self.prompts[l]) for l in Level
        }
        self.sel = sel
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    async def run(
        self,
        context_levels: list[Level],
        cache_policies: list[CachePolicy],
        gather=asyncio.gather,
    ) -> RecursiveResult | None:
        """
        Run the content generation for the configured selection.
        Applies cache policies and generates the result for the root node.
        """
        for policy in cache_policies:
            self.sel.apply_cache_policy(policy)
        return await self._generate(self.sel.root, set(context_levels), gather)

    async def _generate(
        self, node: Node, context_levels: set[Level], gather=asyncio.gather
    ) -> RecursiveResult | None:
        """
        Recursively generate content for the given node and its sources.
        Returns a RecursiveResult or None if no content is available.
        """
        target_page = self.get_target_page(node)

        if node.use_cache and target_page and target_page.path.exists():
            return RecursiveResult(
                dates=list(node.dates),
                output=target_page.content(),
                page=target_page,
            )

        sources = list(sorted(node.sources))

        source_results = await gather(
            *[
                self._generate(source, context_levels, gather)
                for source in sources
                if source.level in context_levels
            ]
        )

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
        frontmatter = dict(
            sys_prompt_hash=md5(sys_prompt),
            model_name=model_name,
            ctime=datetime.now().isoformat(),
            user_prompt_hash=md5("\n".join(source_content)),
            request_tokens=usage.request_tokens,
            response_tokens=usage.response_tokens,
            total_tokens=usage.total_tokens,
            details=usage.details,
            requests=usage.requests,
        )

        output = await prepare_output(node, result, target_page)
        await self.save_page(
            target_page, output, sources, context_levels, frontmatter, node.page
        )
        return RecursiveResult(
            dates=list(node.dates), output=output, page=target_page
        )

    @staticmethod
    async def save_page(
        target_page, output, sources, levels, frontmatter, source_page=None
    ):
        """
        Save the generated page to disk, including frontmatter and source references.
        If the file already exists, it will be renamed with a progressive number.
        """
        # ensure parent directory exists
        target_page.path.parent.mkdir(parents=True, exist_ok=True)

        if target_page.path.exists():
            # Find the next available progressive number
            i = 1
            while True:
                new_path = target_page.path.with_suffix(
                    f".{i}{target_page.path.suffix}"
                )
                if not new_path.exists():
                    target_page.path.rename(new_path)
                    break
                i += 1

        logger.info(
            "Writing generated page %s",
            target_page.path,
        )
        with target_page.path.open("w") as fd:
            source_items = []
            if source_page:
                source_items.append(f"[[{source_page.name}]]")
            for n in sources:
                if not n.retro_page:
                    continue
                if n.level in levels:
                    source_items.append(f"[[{n.retro_page.name}]]")

            frontmatter["sources"] = source_items
            fd.write("---\n")
            fd.write(yaml.dump(frontmatter, default_flow_style=False))
            fd.write("---\n")
            fd.write(output)
