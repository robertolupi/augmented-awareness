import enum
import asyncio
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import PosixPath
from textwrap import dedent

from pydantic_ai import Agent
from pydantic_ai.models import Model

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

    def __eq__(self, other):
        return isinstance(other, Node) and (self.retro_page == other.retro_page)

    def __hash__(self):
        return hash(self.retro_page)

    def __lt__(self, other):
        if not isinstance(other, Node):
            return NotImplemented
        return self.retro_page.name < other.retro_page.name


def build_retrospective_tree(vault: Vault, dates: list[date]) -> dict[Page, Node]:
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


def load_prompt(level: Level):
    with open(PosixPath(__file__).parent / 'retro' / (level.name + ".md")) as fd:
        return fd.read()


class RecursiveRetrospectiveGenerator:
    def __init__(self, model: Model, vault: Vault, dates: list[date], level: Level):
        self.agents = self.create_agents(model)
        self.vault = vault
        self.tree = build_retrospective_tree(vault, dates)
        self.dates = dates
        self.max_level = level

    @staticmethod
    def create_agents(model):
        return {l: Agent(model=model, system_prompt=load_prompt(l)) for l in Level}

    async def run(self, no_cache: int, context_levels: list[Level],
                  gather=asyncio.gather) -> RetrospectiveResult | None:
        retro_page = self.vault.retrospective_page(self.dates[0], self.max_level)
        node = self.tree[retro_page]
        return await self._generate(node, no_cache, set(context_levels), gather)

    async def _generate(self, node: Node, no_cache: int, context_levels: set[Level],
                        gather=asyncio.gather) -> RetrospectiveResult | None:
        if no_cache <= 0 and node.retro_page:
            return RetrospectiveResult(dates=list(node.dates), output=node.retro_page.content(), page=node.retro_page)

        sources = list(sorted(node.sources))

        source_results = await gather(
            *[self._generate(source, no_cache - 1, context_levels, gather) for source in sources
              if node.level in context_levels])

        source_content = [result.output for result in source_results if result]
        if node.page:
            source_content.insert(0, node.page.content())
        if not source_content:
            return None

        result = await self.agents[node.level].run(user_prompt='\n---\n'.join(source_content))

        output = await self.prepare_output(node, result)
        await self.save_retro_page(node, output, sources)
        return RetrospectiveResult(dates=list(node.dates), output=output, page=node.retro_page)

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
    async def save_retro_page(node, output, sources):
        with node.retro_page.path.open('w') as fd:
            fd.write("---\n")
            fd.write("sources:\n")
            if node.page:
                fd.write(f"- \"[[{node.page.name}]]\"\n")
            for n in sources:
                if n.retro_page:
                    fd.write(f"- \"[[{n.retro_page.name}]]\"\n")
            fd.write("---\n")
            fd.write(output)
