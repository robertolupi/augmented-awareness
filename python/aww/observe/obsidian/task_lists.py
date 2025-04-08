"""Mistune plugin to parse Obsidian tasks."""

from datetime import datetime
import re
from typing import Any, Dict, Iterable

from mistune.core import BaseRenderer, BlockState
from mistune.markdown import Markdown

TASK_LIST_ITEM = re.compile(r"^(\[[ xX]\])\s+")

DATE_COMPLETED_RE = re.compile(r"✅\s+(\d{4}-\d{2}-\d{2})")
DATE_CREATED_RE = re.compile(r"➕\s+(\d{4}-\d{2}-\d{2})")
DATE_DUE_RE = re.compile(r"📅\s+(\d{4}-\d{2}-\d{2})")
DATE_STARTED_RE = re.compile(r"🛫\s+(\d{4}-\d{2}-\d{2})")
DATE_SCHEDULED_RE = re.compile(r"⏳\s+(\d{4}-\d{2}-\d{2})")
RECURRENCE_RE = re.compile(r"🔁\s+(.+)")


def task_lists_hook(md: Markdown, state: BlockState) -> Iterable[Dict[str, Any]]:
    return _rewrite_all_list_items(state.tokens)


def render_task_list_item(
    renderer: BaseRenderer, text: str, checked: bool = False
) -> str:
    checkbox = '<input class="task-list-item-checkbox" type="checkbox" disabled'
    if checked:
        checkbox += " checked/>"
    else:
        checkbox += "/>"

    if text.startswith("<p>"):
        text = text.replace("<p>", "<p>" + checkbox, 1)
    else:
        text = checkbox + text

    return '<li class="task-list-item">' + text + "</li>\n"


def task_lists_plugin(md: Markdown) -> None:
    """A mistune plugin to support task lists. Spec defined by
    GitHub flavored Markdown and commonly used by many parsers:

    .. code-block:: text

        - [ ] unchecked task
        - [x] checked task

    :param md: Markdown instance
    """
    md.before_render_hooks.append(task_lists_hook)
    if md.renderer and md.renderer.NAME == "html":
        md.renderer.register("task_list_item", render_task_list_item)


def _rewrite_all_list_items(
    tokens: Iterable[Dict[str, Any]],
) -> Iterable[Dict[str, Any]]:
    for tok in tokens:
        if tok["type"] == "list_item":
            _rewrite_list_item(tok)
        if "children" in tok:
            _rewrite_all_list_items(tok["children"])
    return tokens


def _rewrite_list_item(tok: Dict[str, Any]) -> None:
    children = tok["children"]
    if children:
        first_child = children[0]
        text = first_child.get("text", "")
        m = TASK_LIST_ITEM.match(text)
        if m:
            mark = m.group(1)
            text = text[m.end() :]

            tok["type"] = "task_list_item"
            tok["attrs"] = {"checked": mark != "[ ]"}

            kwargs_re = {
                "created": DATE_CREATED_RE,
                "due": DATE_DUE_RE,
                "started": DATE_STARTED_RE,
                "scheduled": DATE_SCHEDULED_RE,
                "completed": DATE_COMPLETED_RE,
            }
            for name, regex in kwargs_re.items():
                match = regex.search(text)
                if match:
                    text = text.replace(match.group(0), "")
                    tok["attrs"][name] = datetime.strptime(
                        match.group(1), "%Y-%m-%d"
                    ).date()
            match = RECURRENCE_RE.search(text)
            if match:
                recurrence = match.group(1).strip()
                text = text.replace(match.group(0), "")
            else:
                recurrence = None
            tok["attrs"]["recurrence"] = recurrence
            text = text.strip()
            tok["attrs"]["name"] = text
            first_child["text"] = text
