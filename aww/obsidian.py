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
    _PAGE_TEMPLATES: dict[Level, str] = {
        Level.daily: "{year}/{month:02d}/{year}-{month:02d}-{day:02d}.md",
        Level.weekly: "{year}/weeks/{year}-W{week:02d}.md",
        Level.monthly: "{year}/months/{year}-{month:02d}.md",
        Level.yearly: "{year}/Y{year}.md",
    }

    _RETRO_TEMPLATES: dict[Level, str] = {
        Level.daily: "{year}/{month:02d}/r{year}-{month:02d}-{day:02d}.md",
        Level.weekly: "{year}/weeks/r{year}-W{week:02d}.md",
        Level.monthly: "{year}/months/r{year}-{month:02d}.md",
        Level.yearly: "{year}/r{year}.md",
    }

    def __init__(self, path: PosixPath, journal_dir: str, retrospectives_dir: str) -> None:
        self.path = path
        self.journal_dir = journal_dir
        self.retrospectives_dir = retrospectives_dir

    def page(self, d: date, level: Level) -> 'Page':
        return self._make_page(d, level, self.journal_dir, self._PAGE_TEMPLATES)

    def retrospective_page(self, d: date, level: Level) -> 'Page':
        return self._make_page(d, level, self.retrospectives_dir, self._RETRO_TEMPLATES)

    # Legacy convenience methods
    def daily_page(self, d: date) -> 'Page':
        return self.page(d, Level.daily)

    def weekly_page(self, d: date) -> 'Page':
        return self.page(d, Level.weekly)

    def monthly_page(self, d: date) -> 'Page':
        return self.page(d, Level.monthly)

    def yearly_page(self, d: date) -> 'Page':
        return self.page(d, Level.yearly)

    def retrospective_daily_page(self, d: date) -> 'Page':
        return self.retrospective_page(d, Level.daily)

    def retrospective_weekly_page(self, d: date) -> 'Page':
        return self.retrospective_page(d, Level.weekly)

    def retrospective_monthly_page(self, d: date) -> 'Page':
        return self.retrospective_page(d, Level.monthly)

    def retrospective_yearly_page(self, d: date) -> 'Page':
        return self.retrospective_page(d, Level.yearly)

    def _make_page(
        self,
        d: date,
        level: Level,
        base_folder: str,
        templates: dict[Level, str],
    ) -> 'Page':
        tpl = templates[level]
        params = {
            "year": d.year,
            "month": d.month,
            "day": d.day,
            "week": d.isocalendar().week,
        }
        subpath = tpl.format(**params)
        return Page(self.path / base_folder / subpath, level)


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
