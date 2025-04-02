"""Observe the content of an Obsidian vault."""

import collections
import datetime
import os
import pathlib
import re
import time
from typing import Iterable

import mistune
import rich
import rich.markdown
import yaml
from pydantic import BaseModel, Field

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^(\d{1,2}:\d{2})\s+(.+)$")
TAGS_RE = re.compile(r"\B#([-/a-zA-Z0-9_]*)")


class Vault:
    """An Obsidian vault."""

    path: pathlib.Path

    def __init__(self, path: pathlib.Path | str):
        self.path = pathlib.Path(path)
        if not self.path.is_dir():
            raise ValueError(f"Path {self.path} is not a directory.")
        if not (self.path / ".obsidian").is_dir():
            raise ValueError(f"Path {self.path} is not an Obsidian vault.")

    def pages(self) -> dict[str, "Page"]:
        """Get the pages in the vault."""
        pages = {}
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith(".md"):
                    page_path = pathlib.Path(root) / file
                    page = Page(page_path)
                    pages[page.name] = page
        return pages

    def journal(self) -> collections.OrderedDict[datetime.date, "Page"]:
        """Get the pages corresponding to dates in the vault."""
        pages = []
        for name, page in self.pages().items():
            if DATE_RE.match(name):
                date = datetime.datetime.strptime(name, "%Y-%m-%d").date()
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


class Task(BaseModel):
    """A task."""

    name: str = Field(description="name of the task")
    done: bool = Field(description="whether the task is done or not completed yet")

    def __str__(self):
        x = "x" if self.done else " "
        return f"- [{x}] {self.name}"

    def __rich__(self):
        return str(self)


class Event(BaseModel):
    """A tracked or scheduled event."""

    name: str = Field(description="description of the event")
    time: datetime.datetime = Field(description="date and time of the event")
    tags: list[str] = Field(description="tags of the event", default_factory=list)
    duration: datetime.timedelta | None = Field(
        description="duration of the event", default=None
    )

    def __str__(self):
        time_str = time.strftime(
            "%Y-%m-%d %H:%M", time.localtime(self.time.timestamp())
        )
        return f"{time_str} {self.name} {self.tags} ({self.duration or ''})"

    def __rich__(self):
        time_str = time.strftime(
            "%Y-%m-%d %H:%M", time.localtime(self.time.timestamp())
        )
        return f"[b]{time_str}[/] {self.name} {self.tags} ({self.duration})"


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
            if tok["type"] == "list":
                for item in tok["children"]:
                    if item["type"] == "task_list_item":
                        tasks.append(
                            Task(
                                name=item["children"][0]["children"][0]["raw"],
                                done=item["attrs"]["checked"],
                            )
                        )
        return tasks

    def events(self) -> [Event]:
        parsed = self.content().parse()
        events = []
        page_date = datetime.datetime.strptime(self.name, "%Y-%m-%d").date()

        for tok in parsed:
            if tok["type"] == "paragraph":
                for child in tok["children"]:
                    if child["type"] == "text":
                        match = TIME_RE.match(child["raw"])
                        if match:
                            time_str, name = match.groups()
                            dt = datetime.datetime.combine(
                                page_date,
                                datetime.datetime.strptime(time_str, "%H:%M").time(),
                            )
                            tags = TAGS_RE.findall(name)
                            events.append(Event(name=name, time=dt, tags=tags))

        for event, prev_event in zip(events[1:], events):
            prev_event.duration = event.time - prev_event.time
        return events

    def tags(self) -> list[str]:
        """Get the tags in the page."""
        parsed = self.content().parse()
        return list(_get_tags(parsed))


def _get_tags(tokens: list) -> Iterable[str]:
    for tok in tokens:
        if tok["type"] == "text":
            yield from TAGS_RE.findall(tok["raw"])
        elif "children" in tok:
            yield from _get_tags(tok["children"])
