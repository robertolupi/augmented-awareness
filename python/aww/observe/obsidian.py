"""Observe the content of an Obsidian vault."""

from typing import TypeVar

from dataclasses import dataclass
import collections
import os
import datetime
import pathlib
import re

import rich
import rich.markdown
import yaml

import mistune


class Vault:
    """An Obsidian vault."""

    path: pathlib.Path

    def __init__(self, path: pathlib.Path | str):
        self.path = pathlib.Path(path)
        if not self.path.is_dir():
            raise ValueError(f"Path {self.path} is not a directory.")
        if not (self.path / ".obsidian").is_dir():
            raise ValueError(f"Path {self.path} is not an Obsidian vault.")

    def pages(self) -> dict[str, 'Page']:
        """Get the pages in the vault."""
        pages = {}
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith(".md"):
                    page_path = pathlib.Path(root) / file
                    page = Page(page_path)
                    pages[page.name] = page
        return pages

    def journal(self) -> collections.OrderedDict[datetime.date, 'Page']:
        """Get the pages corresponding to dates in the vault."""
        DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        pages = []
        for pagename, page in self.pages().items():
            if DATE_RE.match(pagename):
                date = datetime.datetime.strptime(pagename, "%Y-%m-%d").date()
                pages.append((date, page))
        pages.sort(key=lambda x: x[0])
        return collections.OrderedDict(pages)


class Markdown(str):
    """A Markdown string."""

    def __rich__(self) -> rich.console.RenderableType:
        return rich.markdown.Markdown(self)

    def parse(self) -> list[dict]:
        from mistune.plugins.task_lists import task_lists
        md = mistune.Markdown(renderer=None, plugins=[task_lists])
        return md(self)


@dataclass
class Task:
    """A task in an Obsidian page."""
    name: str
    done: bool


class Page:
    """An Obsidian page."""

    path: pathlib.Path

    def __init__(self, path: pathlib.Path):
        self.path = path

    @property
    def name(self) -> str:
        """Get the name of the page."""
        return self.path.stem

    def frontmatter(self) -> dict:
        """Get the frontmatter of the page."""
        with open(self.path, "r", encoding="utf-8") as f:
            content = f.read()
        if content.startswith("---\n"):
            _, frontmatter, _ = content.split("---\n", 2)
            return yaml.safe_load(frontmatter)
        return {}

    def content(self) -> Markdown:
        """Get the content of the page."""
        with open(self.path, "r", encoding="utf-8") as f:
            content = f.read()
        if content.startswith("---\n"):
            _, _, content = content.split("---\n", 2)
        return Markdown(content)

    def tasks(self) -> [Task]:
        """Get the tasks in the page."""
        parsed = self.content().parse()
        tasks = []
        for tok in parsed:
            if tok['type'] == 'list':
                for item in tok['children']:
                    if item['type'] == 'task_list_item':
                        tasks.append(Task(item['children'][0]['children'][0]['raw'], item['attrs']['checked']))
        return tasks
