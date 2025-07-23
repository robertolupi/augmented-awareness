import enum
import asyncio
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import PosixPath
from textwrap import dedent
from typing import Callable, Dict, Sequence

from pydantic_ai import Agent
from pydantic_ai.models import Model

import yaml

from aww.obsidian import Vault, Page, Level

MARKDOWN_RE = re.compile('```markdown\n(.*?)\n```', re.DOTALL | re.MULTILINE)


@dataclass
class RetrospectiveResult:
    dates: list[date]
    output: str
    page: Page


@dataclass
class Node:
    dates: set[date]
    level: Level
    retro_page: Page
    page: Page
    sources: set['Node']
    use_cache: bool = True

    def __eq__(self, other):
        return isinstance(other, Node) and (self.retro_page == other.retro_page)

    def __hash__(self):
        return hash(self.retro_page)

    def __lt__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.retro_page.name < other.retro_page.name


Tree = Dict[Page, Node]


def build_retrospective_tree(vault: Vault, dates: list[date]) -> Tree:
    tree = {}
    for d in dates:
        for l in Level:
            retro_page = vault.retrospective_page(d, l)
            if retro_page not in tree:
                r = Node(dates=set(), level=l, retro_page=retro_page, page=vault.page(d, l), sources=set())
                tree[retro_page] = r
            else:
                r = tree[retro_page]
            r.dates.add(d)
            for i in Level:
                if i == l:
                    break
                prev_retro_page = vault.retrospective_page(d, i)
                r.sources.add(tree[prev_retro_page])
    return tree


import logging
from functools import cache

logger = logging.getLogger(__name__)

CachePolicy = Callable[[Node, Tree], None]


class NoRootCachePolicy(CachePolicy):
    def __call__(self, node: Node, tree: Tree):
        node.use_cache = False


class NoLevelsCachePolicy(CachePolicy):
    def __init__(self, levels: Sequence[Level]):
        self.levels = set(levels)

    def __call__(self, node: Node, tree: Tree):
        for source in node.sources:
            if source.level in self.levels:
                source.use_cache = False


class ModificationTimeCachePolicy(CachePolicy):
    def __call__(self, node: Node, tree: Tree):
        for node in tree.values():
            if not node.page or not node.retro_page:
                continue
            if node.page.mtime_ns() > node.retro_page.mtime_ns():
                node.use_cache = False


class RecursiveRetrospectiveGenerator:
    def __init__(self, model: Model, vault: Vault, dates: list[date], level: Level, concurrency_limit: int = 10,
                 prompts_path: PosixPath | None = None):
        self.agents = self.create_agents(model, prompts_path or (PosixPath(__file__).parent / 'retro'))
        self.vault = vault
        self.tree = build_retrospective_tree(vault, dates)
        self.dates = dates
        self.max_level = level
        self.semaphore = asyncio.Semaphore(concurrency_limit)

    @staticmethod
    def create_agents(model, prompts_path: PosixPath):
        def load_prompt(level: Level):
            path = prompts_path / f"{level.name}.md"
            return path.read_text()

        return {l: Agent(model=model, system_prompt=load_prompt(l)) for l in Level}

    async def run(self, context_levels: list[Level],
                  cache_policies: list[CachePolicy],
                  gather=asyncio.gather) -> RetrospectiveResult | None:
        retro_page = self.vault.retrospective_page(self.dates[0], self.max_level)
        node = self.tree[retro_page]
        for policy in cache_policies:
            policy(node, self.tree)
        return await self._generate(node, set(context_levels), gather)

    async def _generate(self, node: Node, context_levels: set[Level],
                        gather=asyncio.gather) -> RetrospectiveResult | None:
        if node.use_cache and node.retro_page:
            return RetrospectiveResult(dates=list(node.dates), output=node.retro_page.content(), page=node.retro_page)

        sources = list(sorted(node.sources))

        source_results = await gather(
            *[self._generate(source, context_levels) for source in sources if source.level in context_levels])

        source_content = [result.output for result in source_results if result]
        if node.page:
            source_content.insert(0, await self.page_content(node))
        if not source_content:
            return None

        async with self.semaphore:
            agent = self.agents[node.level]
            sys_prompt = agent.system_prompt()
            model_name = agent.model.model_name
            user_prompt = '\n---\n'.join(source_content)
            retro_frontmatter = dict(
                sys_prompt_hash=hex(hash(sys_prompt)),
                model_name=model_name,
                ctime=datetime.now().isoformat(),
                user_prompt_hash=hex(hash(user_prompt)),
            )
            result = await agent.run(user_prompt=user_prompt)

        output = await self.prepare_output(node, result)
        await self.save_retro_page(node, output, sources, context_levels, retro_frontmatter)
        return RetrospectiveResult(dates=list(node.dates), output=output, page=node.retro_page)

    @staticmethod
    async def page_content(node):
        page_content = [f'Page: [[{node.page.name}]]', node.page.content()]
        if fm := node.page.frontmatter():
            if 'stress' in fm and fm['stress'] is not None:
                page_content.append(f"Stress level {fm['stress']} of 10.")
            if 'kg' in fm and fm['kg'] is not None:
                page_content.append(f"Weight {fm['kg']} kg.")
            if 'bmi' in fm and fm['bmi'] is not None:
                page_content.append(f"Body Mass Index (BMI) {fm['bmi']}.")
            for i in ('sleep_score', 'vitals_score', 'activity_score', 'relax_score'):
                if i in fm and fm[i] is not None:
                    label = i.replace('_', ' ').capitalize()
                    page_content.append(f"{label} {fm[i]} of 100.")
        return '\n'.join(page_content)

    @staticmethod
    async def prepare_output(node, result):
        output = result.output.strip()
        if m := MARKDOWN_RE.match(output):
            output = m.group(1)
        output = output.replace('![[', '[[')
        output_title = f"# {node.retro_page.name}"
        output = output_title + "\n\n" + output
        return output

    @staticmethod
    async def save_retro_page(node, output, sources, levels, retro_frontmatter):
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
                if n in sources and n.level in levels:
                    source_items.append(f"[{n.retro_page.name}]")

            retro_frontmatter['sources'] = source_items
            fd.write("---\n")
            fd.write(yaml.dump(retro_frontmatter, default_flow_style=False))
            fd.write("---\n")
            fd.write(output)
