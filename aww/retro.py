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
        self.agents = {l: Agent(model=model, system_prompt=load_prompt(l)) for l in Level}
        self.vault = vault
        self.tree = build_retrospective_tree(vault, dates)
        self.dates = dates
        self.max_level = level

    async def run(self, no_cache: int, gather=asyncio.gather) -> RetrospectiveResult | None:
        retro_page = self.vault.retrospective_page(self.dates[0], self.max_level)
        node = self.tree[retro_page]
        return await self._generate(node, no_cache, gather)

    async def _generate(self, node: Node, no_cache: int, gather=asyncio.gather) -> RetrospectiveResult | None:
        if no_cache <= 0 and node.retro_page:
            return RetrospectiveResult(dates=list(node.dates), output=node.retro_page.content(), page=node.retro_page)

        source_content = []
        if node.page:
            source_content.append(node.page.content())
        source_generation = [self._generate(source, no_cache - 1, gather) for source in node.sources]
        source_results = await gather(*source_generation)
        for result in source_results:
            if result:
                source_content.append(result.output)
        if not source_content:
            return None
        result = await self.agents[node.level].run(user_prompt='\n---\n'.join(source_content))
        output = result.output.strip()
        if m := MARKDOWN_RE.match(output):
            output = m.group(1)
        output = output.replace('![[', '[[')
        with node.retro_page.path.open('w') as fd:
            fd.write("---\n")
            fd.write("sources:\n")
            for n in node.sources:
                fd.write(f"- [[{n.retro_page.name}]]\n")
            fd.write("---\n")
            fd.write(output)
        return RetrospectiveResult(dates=list(node.dates), output=output, page=node.retro_page)
