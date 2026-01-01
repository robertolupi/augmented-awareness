"""
Obsidian vault and note structure utilities for Augmented Awareness.
Provides classes and functions for working with Obsidian-style markdown vaults, pages, and retrospectives.
"""

import enum
import os
import re
from datetime import date, time
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from aww.config import Settings

FRONTMATTER_RE = re.compile("^---\n(.*?)\n---\n", re.DOTALL | re.MULTILINE)
CODEBLOCKS_RE = re.compile("\n```([a-z]+)\n(.*?)\n```\n", re.DOTALL | re.MULTILINE)


class Level(enum.Enum):
    """Enumeration of note/retrospective levels (daily, weekly, monthly, yearly)."""

    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


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

    @classmethod
    def from_settings(cls, settings: Settings) -> "Vault":
        return cls(
            settings.vault_path, settings.journal_dir, settings.retrospectives_dir
        )

    def __init__(
        self, path: Path | str, journal_dir: str, retrospectives_dir: str
    ) -> None:
        """Initialize the vault with root path and subdirectories for journals and retrospectives."""
        self.path = Path(path).expanduser()
        if not self.path.exists():
            raise FileNotFoundError(self.path)
        self.journal_dir = journal_dir
        self.retrospectives_dir = retrospectives_dir

    def page(self, d: date, level: Level) -> "Page":
        """Return the journal Page for the given date and level."""
        return self._make_page(d, level, self.journal_dir, self._PAGE_TEMPLATES)

    def page_by_name(self, name: str) -> "Page":
        for page in self.walk():
            if page.name == name:
                return page
        raise ValueError(f"Page with name '{name}' not found in vault")

    def retrospective_page(self, d: date, level: Level) -> "Page":
        """Return the retrospective Page for the given date and level."""
        return self._make_page(d, level, self.retrospectives_dir, self._RETRO_TEMPLATES)

    def _make_page(
        self,
        d: date,
        level: Level,
        base_folder: str,
        templates: dict[Level, str],
    ) -> "Page":
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

    def walk(self):
        """Walk over all markdown files in the vault."""
        for root, dirs, files in os.walk(self.path):
            for file in files:
                if file.endswith(".md"):
                    yield Page(Path(root) / file, None)


class Page:
    """
    Represents a single markdown page in the vault, with helpers for content, frontmatter, and metadata.
    """

    def __init__(self, path: Path, level: Level | None = None):
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

    def __eq__(self, other: object):
        """Equality based on file path."""
        return isinstance(other, Page) and (self.path == other.path)

    def __hash__(self):
        """Hash based on file path."""
        return hash(self.path)

    def __bool__(self):
        """Page is truthy if the file exists."""
        return self.path.exists()

    def mtime_ns(self) -> int:
        """Return the file's modification time in nanoseconds."""
        return self.path.stat().st_mtime_ns

    def content(self) -> str:
        """Return the page content, with frontmatter and code blocks removed."""
        with self.path.open() as fd:
            data = fd.read()
        data = FRONTMATTER_RE.sub("", data)
        data = CODEBLOCKS_RE.sub("", data)
        return data

    def enumerate_content_lines(self):
        with self.path.open() as fd:
            lines = enumerate(fd.readlines())
        in_frontmatter = False
        for n, line in lines:
            if n == 0 and line == "---\n":
                in_frontmatter = True
                continue
            if in_frontmatter:
                if line == "---\n":
                    in_frontmatter = False
                continue
            yield n, line.strip()

    def events(self) -> pd.DataFrame:
        line_numbers = []
        start_times = []
        end_times = []
        descriptions = []
        for n, line in self.enumerate_content_lines():
            m = EVENT_RE.match(line)
            if not m:
                continue
            line_numbers.append(n)
            start_hour, start_minute, end_hour, end_minute, description = m.groups()
            start_times.append(time(int(start_hour), int(start_minute)))
            if end_hour is not None:
                end_times.append(time(int(end_hour), int(end_minute)))
            else:
                end_times.append(None)
            descriptions.append(description)
        return pd.DataFrame(
            {
                "start": start_times,
                "end": end_times,
                "description": descriptions,
            },
            index=line_numbers,
        )

    def tasks(self) -> pd.DataFrame:
        line_numbers = []
        statuses = []
        descriptions = []
        for n, line in self.enumerate_content_lines():
            m = TASK_RE.match(line)
            if not m:
                continue
            line_numbers.append(n)
            statuses.append(m.group(1))
            descriptions.append(m.group(2))
        return pd.DataFrame(
            {"status": statuses, "description": descriptions}, index=line_numbers
        )

    def frontmatter(self) -> dict[str, Any]:
        """Return the parsed YAML frontmatter as a dict."""
        with self.path.open() as fd:
            data = fd.read()
        if m := FRONTMATTER_RE.match(data):
            try:
                frontmatter = yaml.safe_load(m.group(1))
                if isinstance(frontmatter, dict):
                    return frontmatter
                return {}
            except yaml.error.YAMLError:
                return {}
        return {}

    def feedback(self) -> list[dict[str, str]]:
        """Return a list of feedback comments found in the page, with context."""
        feedback_items = []
        context_buffer = []
        for _, line in self.enumerate_content_lines():
            if m := FEEDBACK_RE.match(line):
                feedback_items.append(
                    {
                        "comment": m.group(1),
                        "context": "\n".join(context_buffer),
                    }
                )
            else:
                context_buffer.append(line)
                if len(context_buffer) > 3:
                    context_buffer.pop(0)
        return feedback_items

    def feedback_score(self) -> int | None:
        """Return the feedback score from the frontmatter, if present."""
        return self.frontmatter().get("feedback_score")


EVENT_RE = re.compile(r"^(\d\d):(\d\d)(?:\s*-\s*(\d\d):(\d\d))?\s+(.*)$")
TASK_RE = re.compile(r"\s*- \[(.)] (.*)$")
FEEDBACK_RE = re.compile(r"^#feedback\s+(.*)$")
