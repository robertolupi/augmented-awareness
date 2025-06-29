"""Observe the content of an Obsidian vault."""

import collections
import datetime
import os
import pathlib
import re
import time
from typing import Iterable, Dict, Any, List

import mistune
import rich
import rich.markdown
import yaml
from pydantic import BaseModel, Field

from aww.settings import Settings
from aww.pyarrow_util import pydantic_to_pyarrow_table
import pyarrow as pa

from .events import events_plugin
from .task_lists import task_lists_plugin

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TIME_RE = re.compile(r"^(\d{1,2}:\d{2})\s+(.+)$")
TAGS_RE = re.compile(r"\B#([-/a-zA-Z0-9_]*)")

DATE_COMPLETED_RE = re.compile(r"✅\s+(\d{4}-\d{2}-\d{2})")
DATE_CREATED_RE = re.compile(r"➕\s+(\d{4}-\d{2}-\d{2})")
DATE_DUE_RE = re.compile(r"📅\s+(\d{4}-\d{2}-\d{2})")
DATE_STARTED_RE = re.compile(r"🛫\s+(\d{4}-\d{2}-\d{2})")
DATE_SCHEDULED_RE = re.compile(r"⏳\s+(\d{4}-\d{2}-\d{2})")
RECURRENCE_RE = re.compile(r"🔁\s+(.+)")


class Markdown(str):
    """A Markdown string."""

    def __rich__(self) -> rich.console.RenderableType:
        return rich.markdown.Markdown(self)

    def parse(self) -> list[dict]:
        md = mistune.Markdown(renderer=None, plugins=[events_plugin, task_lists_plugin])
        return md(self)


class Task(BaseModel):
    """A task."""

    name: str = Field(description="name of the task")
    done: bool = Field(description="whether the task is done or not completed yet")
    created: datetime.date | None = Field(
        description="date the task was created", default=None
    )
    due: datetime.date | None = Field(description="date the task is due", default=None)
    started: datetime.date | None = Field(
        description="date the task was started", default=None
    )
    scheduled: datetime.date | None = Field(
        description="date the task was scheduled", default=None
    )
    completed: datetime.date | None = Field(
        description="date the task was completed", default=None
    )
    recurrence: str | None = Field(description="recurrence of the task", default=None)

    def _string_repr(self, name: str, captions: list):
        x = "x" if self.done else " "
        details = []
        for prefix, field_name in captions:
            if getattr(self, field_name):
                details.append(f"{prefix} {getattr(self, field_name)}")
        details_str = ", ".join(details)
        return f"- [{x}] {name}" + (f" ({details_str})" if details else "")

    def __str__(self):
        return self._string_repr(
            self.name,
            [
                ("created", "created"),
                ("scheduled", "scheduled"),
                ("started", "started"),
                ("due", "due"),
                ("completed", "completed"),
            ],
        )

    def __rich__(self):
        return self._string_repr(
            f"[b]{self.name}[/]",
            [
                ("➕", "created"),
                ("⏳", "scheduled"),
                ("🛫", "started"),
                ("📅", "due"),
                ("✅", "completed"),
            ],
        )


class Event(BaseModel):
    """A tracked or scheduled event."""

    name: str = Field(description="description of the event")
    time: datetime.datetime = Field(description="date and time of the event")
    tags: list[str] = Field(description="tags of the event", default_factory=list)
    duration: datetime.timedelta | None = Field(
        description="duration of the event", default=None
    )
    status: str = Field(
        description="event status or type ('<'=scheduled, '-'=cancelled, ''=normal, etc.)",
        default="",
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


class Section:
    """A section in an Obsidian page."""

    def __init__(self, path: pathlib.Path, header_re: str):
        self.path = path
        self.header_re = header_re
        lines = open(self.path, "r").readlines()
        starts, ends = self.get_section(lines)
        self.lines = lines[starts:ends]

    def save(self):
        lines = open(self.path, "r").readlines()
        starts, ends = self.get_section(lines)
        lines[starts:ends] = self.lines
        with open(self.path, "w") as fd:
            fd.write("".join(lines))

    def get_section(self, lines: List[str]):
        header_re = re.compile("^(#+)\\s+" + self.header_re + "$")
        section_start = None
        if not lines:
            raise ValueError("page content is empty")
        for n, line in enumerate(lines):
            if m := header_re.match(line):
                section_start = m.group(1) + " "
                break
        if not section_start:
            raise ValueError(f"page doesn't contain the section: {self.header_re}")
        section = None
        for k in range(n + 1, len(lines)):
            if lines[k].startswith(section_start):
                section = (n + 1, k)
                break
        if not section:
            section = (n + 1, len(lines))
        return section


class Page:
    """An Obsidian page."""

    path: pathlib.Path

    def __init__(self, path: pathlib.Path):
        self.path = path

    @property
    def name(self) -> str:
        """Get the name of the page."""
        return self.path.stem

    @property
    def modified_time(self) -> datetime.datetime:
        """Get the last modified date of the page."""
        return datetime.datetime.fromtimestamp(self.path.stat().st_mtime)

    @property
    def created_time(self) -> datetime.datetime:
        """Get the creation date of the page."""
        return datetime.datetime.fromtimestamp(self.path.stat().st_ctime)

    @property
    def access_time(self) -> datetime.datetime:
        """Get the last access date of the page."""
        return datetime.datetime.fromtimestamp(self.path.stat().st_atime)

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

    def get_section(self, header_re: str) -> Section | None:
        """Get the content of a section of the page, by the header name."""
        try:
            return Section(self.path, header_re)
        except ValueError:
            return None

    def tasks(self) -> Iterable[Task]:
        """Get the tasks in the page."""
        parsed = self.content().parse()
        for tok in parsed:
            if tok["type"] == "list":
                for item in tok["children"]:
                    if item["type"] == "task_list_item":
                        kwargs = {}
                        for key in (
                            "created",
                            "due",
                            "started",
                            "scheduled",
                            "completed",
                            "recurrence",
                        ):
                            if date := item["attrs"].get(key):
                                kwargs[key] = date

                        yield Task(
                            name=item["attrs"]["name"],
                            done=item["attrs"]["checked"],
                            **kwargs,
                        )

    def events(self) -> Iterable[Event]:
        parsed = self.content().parse()
        page_date = datetime.datetime.strptime(self.name, "%Y-%m-%d").date()

        for event in _get_all(parsed, "event"):
            time_str = event["attrs"]["time"]
            end_time_str = event["attrs"]["end_time"]
            name = event["attrs"]["name"]
            tags = event["attrs"]["tags"]
            status = event["attrs"]["status"] or ""
            dt = datetime.datetime.combine(
                page_date, datetime.datetime.strptime(time_str, "%H:%M").time()
            )
            if end_time_str:
                de = datetime.datetime.combine(
                    page_date, datetime.datetime.strptime(end_time_str, "%H:%M").time()
                )
                duration = de - dt
            else:
                duration = None
            yield Event(name=name, time=dt, tags=tags, duration=duration, status=status)

    def tags(self) -> list[str]:
        """Get the tags in the page."""
        parsed = self.content().parse()
        return list(_get_tags(parsed))


def _get_all(token: Iterable[Dict[str, Any]], typ: str) -> Iterable[Dict[str, Any]]:
    for tok in token:
        if tok["type"] == typ:
            yield tok
        elif "children" in tok:
            yield from _get_all(tok["children"], typ)


def _get_tags(tokens: list) -> Iterable[str]:
    for tok in tokens:
        match tok["type"]:
            case "text":
                yield from TAGS_RE.findall(tok["raw"])
            case "event":
                yield from tok["attrs"]["tags"]

        if "children" in tok:
            yield from _get_tags(tok["children"])


class Journal(collections.OrderedDict[datetime.date, "Page"]):
    """An Obsidian journal.

    The pages are ordered by date.
    """

    def subrange(
        self,
        start: datetime.date | datetime.datetime,
        end: datetime.date | datetime.datetime,
    ) -> "Journal":
        """Get a subrange of the journal."""
        journal = Journal()
        if isinstance(start, datetime.datetime):
            start = start.date()
        if isinstance(end, datetime.datetime):
            end = end.date()
        for date, page in self.items():
            if start <= date <= end:
                journal[date] = page
            if date > end:
                break
        return journal

    def __repr__(self):
        dates = list(self.keys())
        return f"Journal(min={dates[0]}, max={dates[-1]}, count={len(dates)})"

    def tasks_table(self) -> pa.Table:
        all_tasks = [task for page in self.values() for task in page.tasks()]
        return pydantic_to_pyarrow_table(all_tasks, Task)

    def event_table(self) -> pa.Table:
        all_events = [event for page in self.values() for event in page.events()]
        return pydantic_to_pyarrow_table(all_events, Event)


class Vault:
    """An Obsidian vault."""

    path: pathlib.Path

    def __init__(self, path: pathlib.Path | str | None = None):
        if path is None:
            path = Settings().obsidian.vault.resolve()
        self.path = pathlib.Path(path)
        if not self.path.is_dir():
            raise ValueError(f"Path {self.path} is not a directory.")
        if not (self.path / ".obsidian").is_dir():
            raise ValueError(f"Path {self.path} is not an Obsidian vault.")

    def pages(self) -> dict[str, Page]:
        """Get the pages in the vault."""
        pages = {}
        for root, _, files in os.walk(self.path):
            for file in files:
                if file.endswith(".md"):
                    page_path = pathlib.Path(root) / file
                    page = Page(page_path)
                    pages[page.name] = page
        return pages

    def journal(self) -> Journal:
        """Get the pages corresponding to dates in the vault."""
        pages = []
        for name, page in self.pages().items():
            if DATE_RE.match(name):
                date = datetime.datetime.strptime(name, "%Y-%m-%d").date()
                pages.append((date, page))
        pages.sort(key=lambda x: x[0])
        return Journal(pages)
