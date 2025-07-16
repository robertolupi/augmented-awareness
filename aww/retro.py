import asyncio
import re
from dataclasses import dataclass
from datetime import date
from pathlib import PosixPath
from textwrap import dedent

from pydantic_ai import Agent
from pydantic_ai.models import Model

from aww.obsidian import Vault, Page

MARKDOWN_RE = re.compile('```markdown\n(.*?)\n```', re.DOTALL | re.MULTILINE)


@dataclass
class RetrospectiveResult:

    def __init__(self, dates: list[date], output: str, page: Page):
        self.dates = dates
        output = output.strip()
        if m := MARKDOWN_RE.match(output):
            output = m.group(1)
        self.output = output
        self.page = page

    dates: list[date]
    output: str
    page: Page


def load_prompt(name: str):
    with open(PosixPath(__file__).parent / 'retro' / name) as fd:
        return fd.read()


class DailyRetrospectiveAgent:
    prompt = load_prompt("daily.md")

    def __init__(self, model: Model, vault: Vault):
        self.vault = vault
        self.agent = Agent(model=model, system_prompt=self.prompt)

    async def run(self, d: date, no_cache: bool = False) -> RetrospectiveResult | None:
        retro_page = self.vault.retrospective_daily_page(d)
        if not no_cache and retro_page.exists():
            return RetrospectiveResult(dates=[d], output=retro_page.content(), page=retro_page)

        page = self.vault.daily_page(d)
        if not page:
            return None
        result = await self.agent.run(user_prompt=page.content())
        retro_result = RetrospectiveResult(dates=[d], output=result.output, page=retro_page)
        self.write(retro_result)
        return retro_result

    def write(self, result: RetrospectiveResult):
        if not result:
            return
        page = result.page
        page.path.parent.mkdir(parents=True, exist_ok=True)
        with page.path.open('w') as fd:
            fd.write(dedent(f"""
            # {page.name}

            """))
            fd.write(result.output)
            fd.write("\n")
            fd.write(dedent(f"""
            ---
            Dates:
            
            """))
            for d in result.dates:
                fd.write(f"- [[{d.isoformat()}]]\n")
            fd.write("\n")


class WeeklyRetrospectiveAgent:
    prompt = load_prompt("weekly.md")

    def __init__(self, model: Model, vault: Vault):
        self.vault = vault
        self.agent = Agent(model=model, system_prompt=self.prompt)
        self.daily_agent = DailyRetrospectiveAgent(model, vault)

    async def run(self, dd: list[date], gather=asyncio.gather, no_cache: bool = False) -> RetrospectiveResult | None:
        if not dd:
            return None

        d = dd[-1]
        retro_page = self.vault.retrospective_weekly_page(d)
        if not no_cache and retro_page.exists():
            return RetrospectiveResult(dates=dd, output=retro_page.content(), page=retro_page)

        daily_tasks = [self.daily_agent.run(d, no_cache=no_cache) for d in dd]
        daily_results = await gather(*daily_tasks)

        content = []
        for result in daily_results:
            if result:
                content.append(result.output)

        seen_pages = set()
        for d in dd:
            page = self.vault.weekly_page(d)
            if page and page not in seen_pages:
                content.append(page.content())
                seen_pages.add(page)

        result = await self.agent.run(user_prompt='\n---\n'.join(content))
        retro_result = RetrospectiveResult(dates=dd, output=result.output, page=retro_page)
        self.write(retro_result)
        return retro_result

    def write(self, result: RetrospectiveResult):
        if not result:
            return
        page = result.page
        page.path.parent.mkdir(parents=True, exist_ok=True)
        with page.path.open('w') as fd:
            fd.write(dedent(f"""
            # {page.name}

            """))
            fd.write(result.output)
            fd.write("\n")
            fd.write(dedent(f"""
            ---
            Dates:
            """))
            for d in result.dates:
                fd.write(f"- [[{d.isoformat()}]] [[r{d.isoformat()}]]\n")
            fd.write("\n")
