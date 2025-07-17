import enum
import os
from datetime import date
import re

from pathlib import PosixPath

FRONTMATTER_RE = re.compile('^---\n(.*?)\n---\n', re.DOTALL | re.MULTILINE)


class Level(enum.Enum):
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'
    yearly = 'yearly'


class Vault:
    def __init__(self, path: PosixPath, journal_dir: str):
        self.path = path
        self.journal_dir = journal_dir

    def page(self, d: date, level: Level):
        match level:
            case Level.daily:
                return self.daily_page(d)
            case Level.weekly:
                return self.weekly_page(d)
            case Level.monthly:
                return self.monthly_page(d)
            case Level.yearly:
                return self.yearly_page(d)
            case _:
                raise ValueError(f"Invalid level: {level}")

    def daily_page(self, d: date):
        page_path = self.path / self.journal_dir / d.strftime('%Y/%m/%Y-%m-%d.md')
        return Page(page_path, Level.daily)

    def weekly_page(self, d: date):
        year = d.year
        week_number = d.isocalendar().week
        page_path = self.path / self.journal_dir / f"{year}/weeks/{year}-W{week_number:02d}.md"
        return Page(page_path, Level.weekly)

    def monthly_page(self, d: date):
        year = d.year
        month = d.month
        page_path = self.path / self.journal_dir / f"{year}/months/{year}-{month:02d}.md"
        return Page(page_path, Level.monthly)

    def yearly_page(self, d: date):
        year = d.year
        page_path = self.path / self.journal_dir / f"{year}/Y{year}.md"
        return Page(page_path, Level.yearly)

    def retrospective_page(self, d: date, level: Level):
        match level:
            case Level.daily:
                return self.retrospective_daily_page(d)
            case Level.weekly:
                return self.retrospective_weekly_page(d)
            case Level.monthly:
                return self.retrospective_monthly_page(d)
            case Level.yearly:
                return self.retrospective_yearly_page(d)
            case _:
                raise ValueError(f"Invalid level: {level}")

    def retrospective_daily_page(self, d: date):
        page_path = self.path / "retrospectives" / d.strftime('%Y/%m') / f"r{d.strftime('%Y-%m-%d')}.md"
        return Page(page_path, Level.daily)

    def retrospective_weekly_page(self, d: date):
        year = d.year
        week_number = d.isocalendar().week
        page_path = self.path / "retrospectives" / f"{year}/weeks" / f"r{year}-W{week_number:02d}.md"
        return Page(page_path, Level.weekly)

    def retrospective_monthly_page(self, d: date):
        year = d.year
        month = d.month
        page_path = self.path / "retrospectives" / f"{year}/months" / f"r{year}-{month:02d}.md"
        return Page(page_path, Level.monthly)

    def retrospective_yearly_page(self, d: date):
        year = d.year
        page_path = self.path / "retrospectives" / f"{year}" / f"r{year}.md"
        return Page(page_path, Level.yearly)


class Page:
    def __init__(self, path: PosixPath, level: Level|None):
        self.path = path
        self.level = level

    @property
    def name(self) -> str:
        return os.path.splitext(self.path.name)[0]

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Page(" + repr(self.path) + ")"

    def __eq__(self, other: 'Page'):
        return isinstance(other, Page) and (self.path == other.path)

    def __hash__(self):
        return hash(self.path)

    def __bool__(self):
        return self.path.exists()

    def exists(self):
        return self.path.exists()

    def mtime_ns(self):
        return self.path.stat().st_mtime_ns

    def content(self):
        with self.path.open() as fd:
            data = fd.read()
        if FRONTMATTER_RE.match(data):
            return FRONTMATTER_RE.sub('', data)
        else:
            return data
