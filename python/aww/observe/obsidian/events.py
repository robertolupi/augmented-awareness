"""Mistune plugin to parse Aww events."""
from typing import Iterable, Dict, Any

import re

from mistune import Markdown
from mistune.core import BlockState

EVENT_RE = re.compile(r"^(\d{1,2}:\d{2})\s+(.+)$")
TAGS_RE = re.compile(r"\B#([-/a-zA-Z0-9_]*)")


def events_plugin(md: Markdown) -> None:
    md.before_render_hooks.append(events_hook)


def events_hook(md: Markdown, state: BlockState) -> Iterable[Dict[str, Any]]:
    return _rewrite_all_events(state.tokens)


def _rewrite_all_events(tokens: Iterable[Dict[str, Any]]) -> Iterable[Dict[str, Any]]:
    for tok in tokens:
        match tok["type"]:
            case "list_item":
                _rewrite_list_item(tok)
            case "paragraph":
                _rewrite_paragraph(tok)

        if "children" in tok:
            _rewrite_all_events(tok["children"])
    return tokens


def _rewrite_list_item(tok: Dict[str, Any]) -> None:
    children = tok["children"]
    if children:
        first_child = children[0]
        text = first_child.get("text", "")
        m = EVENT_RE.match(text)
        if m:
            time = m.group(1)
            name = m.group(2)
            first_child["text"] = text[m.end():]

            tags = TAGS_RE.findall(text)

            tok["type"] = "event"
            tok["attrs"] = {"time": time, "name": name, "tags": tags}


def _rewrite_paragraph(tok: Dict[str, Any]) -> None:
    text = tok.get("text", "")
    lines = text.splitlines()
    events = []
    for line in lines:
        m = EVENT_RE.match(line)
        if m:
            time = m.group(1)
            name = m.group(2)
            line = line[m.end():]
            tags = TAGS_RE.findall(name)
            event = {"type": "event", "text": line, "attrs": {"time": time, "name": name, "tags": tags}}
            events.append(event)
    if events:
        if not "children" in tok:
            tok["children"] = []
        tok["children"].extend(events)
