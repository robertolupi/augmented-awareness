import asyncio
from dataclasses import dataclass
from datetime import date
from pathlib import PosixPath
from textwrap import dedent

from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model

from aww.obsidian import Vault


@dataclass
class RetrospectiveResult:
    dates: list[date]
    output: str


def load_prompt(name: str):
    with open(PosixPath(__file__).parent / 'retro' / name) as fd:
        return fd.read()


class DailyRetrospectiveAgent:
    prompt = load_prompt("daily.md")

    def __init__(self, model: Model, vault: Vault):
        self.vault = vault
        self.agent = Agent(model=model, system_prompt=self.prompt)

    async def run(self, d: date) -> RetrospectiveResult | None:
        page = self.vault.daily_page(d)
        if not page:
            return None
        result = await self.agent.run(user_prompt=page.content())
        return RetrospectiveResult(dates=[d], output=result.output)


class WeeklyRetrospectiveAgent:
    prompt = load_prompt("weekly.md")

    def __init__(self, model: Model, vault: Vault):
        self.vault = vault
        self.agent = Agent(model=model, system_prompt=self.prompt)
        self.daily_agent = DailyRetrospectiveAgent(model, vault)

    async def run(self, dd: list[date], gather=asyncio.gather) -> RetrospectiveResult | None:
        if not dd:
            return None

        daily_tasks = [self.daily_agent.run(d) for d in dd]
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
        return RetrospectiveResult(dates=dd, output=result.output)