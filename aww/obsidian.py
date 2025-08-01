
"""
Obsidian vault and note structure utilities for Augmented Awareness.
Provides classes and functions for working with Obsidian-style markdown vaults, pages, and retrospectives.
"""

import enum
import os
from dataclasses import dataclass
from datetime import date
import re
from typing import Dict

import yaml

from pathlib import Path

FRONTMATTER_RE = re.compile('^---\n(.*?)\n---\n', re.DOTALL | re.MULTILINE)
CODEBLOCKS_RE = re.compile('\n```([a-z]+)\n(.*?)\n```\n', re.DOTALL | re.MULTILINE)


class Level(enum.Enum):
    """Enumeration of note/retrospective levels (daily, weekly, monthly, yearly)."""
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'
    yearly = 'yearly'


class Vault:
    """
    Represents an Obsidian vault, providing methods to access journal and retrospective pages
    at various levels (daily, weekly, monthly, yearly).
    """
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

    def __init__(self, path: Path, journal_dir: str, retrospectives_dir: str) -> None:
        """Initialize the vault with root path and subdirectories for journals and retrospectives."""
        self.path = path
        self.journal_dir = journal_dir
        self.retrospectives_dir = retrospectives_dir

    def page(self, d: date, level: Level) -> 'Page':
        """Return the journal Page for the given date and level."""
        return self._make_page(d, level, self.journal_dir, self._PAGE_TEMPLATES)

    def retrospective_page(self, d: date, level: Level) -> 'Page':
        """Return the retrospective Page for the given date and level."""
        return self._make_page(d, level, self.retrospectives_dir, self._RETRO_TEMPLATES)

    def _make_page(
            self,
            d: date,
            level: Level,
            base_folder: str,
            templates: dict[Level, str],
    ) -> 'Page':
        """Helper to construct a Page object for the given date, level, folder, and template mapping."""
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
    """
    Represents a single markdown page in the vault, with helpers for content, frontmatter, and metadata.
    """
    def __init__(self, path: Path, level: Level | None):
        """Initialize a Page with its file path and level."""
        self.path = path
        self.level = level

    @property
    def name(self) -> str:
        """Return the page name (filename without extension)."""
        return os.path.splitext(self.path.name)[0]

    def __str__(self):
        """String representation: page name."""
        return self.name

    def __repr__(self):
        """Debug representation: Page(path)."""
        return "Page(" + repr(self.path) + ")"

    def __eq__(self, other: 'Page'):
        """Equality based on file path."""
        return isinstance(other, Page) and (self.path == other.path)

    def __hash__(self):
        """Hash based on file path."""
        return hash(self.path)

    def __bool__(self):
        """Page is truthy if the file exists."""
        return self.path.exists()

    def mtime_ns(self):
        """Return the file's modification time in nanoseconds."""
        return self.path.stat().st_mtime_ns

    def content(self):
        """Return the page content, with frontmatter and code blocks removed."""
        with self.path.open() as fd:
            data = fd.read()
        data = FRONTMATTER_RE.sub('', data)
        data = CODEBLOCKS_RE.sub('', data)
        return data

    def frontmatter(self):
        """Return the parsed YAML frontmatter as a dict, or None if not present or invalid."""
        with self.path.open() as fd:
            data = fd.read()
        if m := FRONTMATTER_RE.match(data):
            try:
                return yaml.load(m.group(1), Loader=yaml.Loader)
            except yaml.error.YAMLError:
                return None
        return None



@dataclass
class Node:
    """
    Represents a node in the retrospective dependency tree.
    Holds references to dates, level, associated pages, sources, and cache usage.
    """
    dates: set[date]
    level: Level
    retro_page: Page
    page: Page
    sources: set['Node']
    use_cache: bool = True

    def __eq__(self, other):
        """Equality based on retro_page."""
        return isinstance(other, Node) and (self.retro_page == other.retro_page)

    def __hash__(self):
        """Hash based on retro_page."""
        return hash(self.retro_page)

    def __lt__(self, other):
        """Order nodes by retro_page name for sorting."""
        if not isinstance(other, Node):
            return NotImplemented
        return self.retro_page.name < other.retro_page.name



Tree = Dict[Page, Node]
"""Type alias for a mapping from Page to Node in the retrospective tree."""


def build_retrospective_tree(vault: Vault, dates: list[date]) -> Tree:
    """
    Build a dependency tree of retrospectives for the given dates and vault.
    Each node represents a retrospective at a given level and date, with sources for lower levels.
    """
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
