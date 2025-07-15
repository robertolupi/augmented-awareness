import os
from datetime import date

from pathlib import PosixPath


class Vault:
    def __init__(self, path: PosixPath, journal_dir: str):
        self.path = path
        self.journal_dir = journal_dir

    def daily_page(self, d: date):
        page_path = self.path / self.journal_dir / d.strftime('%Y/%m/%Y-%m-%d.md')
        return Page(page_path)


class Page:
    def __init__(self, path: PosixPath):
        self.path = path

    @property
    def name(self) -> str:
        return os.path.splitext(self.path.name)[0]

    def __eq__(self, other: 'Page'):
        return isinstance(other, Page) and (self.path == other.path)

    def __hash__(self):
        return hash(self.path)

    def __bool__(self):
        return self.path.exists()
