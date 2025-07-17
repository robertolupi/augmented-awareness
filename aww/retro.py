import enum
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


class Level(enum.Enum):
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'
    yearly = 'yearly'

def load_prompt(level: Level):
    with open(PosixPath(__file__).parent / 'retro' / (level.name + ".md")) as fd:
        return fd.read()


class DailyRetrospectiveAgent:
    prompt = load_prompt(Level.daily)

    def __init__(self, model: Model, vault: Vault):
        self.vault = vault
        self.agent = Agent(model=model, system_prompt=self.prompt)

    async def run(self, d: date, no_cache: int = 0) -> RetrospectiveResult | None:
        page = self.vault.daily_page(d)
        if not page:
            return None

        retro_page = self.vault.retrospective_daily_page(d)
        if no_cache <= 0 and retro_page.exists():
            return RetrospectiveResult(dates=[d], output=retro_page.content(), page=retro_page)

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
    prompt = load_prompt(Level.weekly)

    def __init__(self, model: Model, vault: Vault):
        self.vault = vault
        self.agent = Agent(model=model, system_prompt=self.prompt)
        self.daily_agent = DailyRetrospectiveAgent(model, vault)

    async def run(self, dd: list[date], gather=asyncio.gather, no_cache: int = 0) -> RetrospectiveResult | None:
        pages = [self.vault.daily_page(d) for d in dd]
        if not any(pages):
            return None

        d = dd[-1]
        retro_page = self.vault.retrospective_weekly_page(d)
        if no_cache <= 0 and retro_page.exists():
            return RetrospectiveResult(dates=dd, output=retro_page.content(), page=retro_page)

        daily_tasks = [self.daily_agent.run(d, no_cache=no_cache - 1) for d in dd]
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


class MonthlyRetrospectiveAgent:
    prompt = load_prompt(Level.monthly)

    def __init__(self, model: Model, vault: Vault):
        self.vault = vault
        self.agent = Agent(model=model, system_prompt=self.prompt)
        self.weekly_agent = WeeklyRetrospectiveAgent(model, vault)

    async def run(self, dd: list[date], gather=asyncio.gather, no_cache: int = 0) -> RetrospectiveResult | None:
        pages = [self.vault.daily_page(d) for d in dd]
        if not any(pages):
            return None

        d = dd[-1]
        retro_page = self.vault.retrospective_monthly_page(d)
        if no_cache <= 0 and retro_page.exists():
            return RetrospectiveResult(dates=dd, output=retro_page.content(), page=retro_page)

        weeks = {}
        for day in dd:
            week_key = (day.year, day.isocalendar().week)
            if week_key not in weeks:
                weeks[week_key] = []
            weeks[week_key].append(day)

        weekly_tasks = [self.weekly_agent.run(week_dates, no_cache=no_cache - 1, gather=gather) for week_dates in
                        weeks.values()]
        weekly_results = await gather(*weekly_tasks)

        content = []
        for result in weekly_results:
            if result:
                content.append(result.output)

        seen_pages = set()
        for d_in_month in dd:
            page = self.vault.monthly_page(d_in_month)
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
            seen_weeks = set()
            for d in result.dates:
                week_page = self.vault.retrospective_weekly_page(d)
                if week_page.name not in seen_weeks:
                    fd.write(f"- [[{week_page.name}]]\n")
                    seen_weeks.add(week_page.name)
            fd.write("\n")


class YearlyRetrospectiveAgent:
    prompt = load_prompt(Level.yearly)

    def __init__(self, model: Model, vault: Vault):
        self.vault = vault
        self.agent = Agent(model=model, system_prompt=self.prompt)
        self.monthly_agent = MonthlyRetrospectiveAgent(model, vault)

    async def run(self, dd: list[date], gather=asyncio.gather, no_cache: int = 0) -> RetrospectiveResult | None:
        pages = [self.vault.daily_page(d) for d in dd]
        if not any(pages):
            return None

        d = dd[-1]
        retro_page = self.vault.retrospective_yearly_page(d)
        if no_cache <= 0 and retro_page.exists():
            return RetrospectiveResult(dates=dd, output=retro_page.content(), page=retro_page)

        months = {}
        for day in dd:
            month_key = (day.year, day.month)
            if month_key not in months:
                months[month_key] = []
            months[month_key].append(day)

        monthly_tasks = [self.monthly_agent.run(month_dates, no_cache=no_cache - 1, gather=gather) for month_dates in
                         months.values()]
        monthly_results = await gather(*monthly_tasks)

        content = []
        for result in monthly_results:
            if result:
                content.append(result.output)

        seen_pages = set()
        for d_in_year in dd:
            page = self.vault.yearly_page(d_in_year)
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
            seen_months = set()
            for d in result.dates:
                month_page = self.vault.retrospective_monthly_page(d)
                if month_page.name not in seen_months:
                    fd.write(f"- [[{month_page.name}]]\n")
                    seen_months.add(month_page.name)
            fd.write("\n")
