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

    def run_sync(self, d: date) -> RetrospectiveResult | None:
        page = self.vault.daily_page(d)
        if not page:
            return None
        result = self.agent.run_sync(user_prompt=page.content())
        return RetrospectiveResult(dates=[d], output=result.output)


class WeeklyRetrospectiveAgent:
    prompt = load_prompt("weekly.md")

    def __init__(self, model: Model, vault: Vault):
        self.vault = vault
        self.agent = Agent(model=model, system_prompt=self.prompt)
        self.daily_agent = DailyRetrospectiveAgent(model, vault)

    def run_sync(self, dd: list[date]) -> RetrospectiveResult | None:
        if not dd:
            return None
        daily = []
        for d in dd:
            result = self.daily_agent.run_sync(d)
            if result:
                daily.append(result.output)

        result = self.agent.run_sync(user_prompt='\n---\n'.join(daily))
        return RetrospectiveResult(dates=dd, output=result.output)
