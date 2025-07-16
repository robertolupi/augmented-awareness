import os
from datetime import date
import re

from pathlib import PosixPath

FRONTMATTER_RE = re.compile('^---\n(.*?)\n---\n', re.DOTALL | re.MULTILINE)


class Vault:
    def __init__(self, path: PosixPath, journal_dir: str):
        self.path = path
        self.journal_dir = journal_dir

    def daily_page(self, d: date):
        page_path = self.path / self.journal_dir / d.strftime('%Y/%m/%Y-%m-%d.md')
        return Page(page_path)

    def weekly_page(self, d: date):
        year = d.year
        week_number = d.isocalendar().week
        page_path = self.path / self.journal_dir / f"{year}/weeks/{year}-W{week_number:02d}.md"
        return Page(page_path)

    def retrospective_daily_page(self, d: date):
        page_path = self.path / "retrospectives" / d.strftime('%Y/%m') / f"r{d.strftime('%Y-%m-%d')}.md"
        return Page(page_path)

    def retrospective_weekly_page(self, d: date):
        year = d.year
        week_number = d.isocalendar().week
        page_path = self.path / "retrospectives" / f"{year}/weeks" / f"r{year}-W{week_number:02d}.md"
        return Page(page_path)


class Page:
    def __init__(self, path: PosixPath):
        self.path = path

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
    
    def content(self):
        with self.path.open() as fd:
            data = fd.read()
        if FRONTMATTER_RE.match(data):
            return FRONTMATTER_RE.sub('', data)
        else:
            return data
