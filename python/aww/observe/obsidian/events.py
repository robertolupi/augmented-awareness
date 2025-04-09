"""Mistune plugin to parse events."""

from typing import Iterable, Dict, Any

import re

from mistune import Markdown
from mistune.core import BlockState

EVENT_RE_BASE = (
    r"(?P<time>\d{1,2}:\d{2})(-(?P<end_time>\d{1,2}:\d{2}))?\s+(?P<name>.+)$"
)
EVENT_RE = re.compile(r"^(?:-\s+)?(?P<status>)" + EVENT_RE_BASE)
EVENT_WITH_STATUS_RE = re.compile(r"^(?:\[(?P<status>.)\]\s+)?" + EVENT_RE_BASE)
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
        text, event = _match_event(text, EVENT_WITH_STATUS_RE)
        if event:
            first_child["text"] = text
            first_child.update(event)


def _rewrite_paragraph(tok: Dict[str, Any]) -> None:
    text = tok.get("text", "")
    lines = text.splitlines()
    events = []
    for line in lines:
        line, event = _match_event(line, EVENT_RE)
        if event:
            event["text"] = line
            events.append(event)
    if events:
        if "children" not in tok:
            tok["children"] = []
        for prev_event, event in zip(events, events[1:]):
            if not prev_event["attrs"]["end_time"]:
                prev_event["attrs"]["end_time"] = event["attrs"]["time"]
        tok["children"].extend(events)


def _match_event(text: str, pattern: re.Pattern[str]):
    m = pattern.match(text)
    if m:
        time = m.group("time")
        name = m.group("name")
        end_time = m.group("end_time")
        status = m.group("status")
        text = text[m.end() :]
        tags = TAGS_RE.findall(name)
        event = {
            "type": "event",
            "attrs": {
                "time": time,
                "end_time": end_time,
                "name": name,
                "tags": tags,
                "status": status,
            },
        }
        return text, event
    return text, None
