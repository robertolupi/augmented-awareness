import datetime
import pathlib

import pytest
import rich
import rich.markdown

from aww.observe.obsidian import Vault
import aww.settings

test_dir = pathlib.Path(__file__).parent
test_vault_dir = test_dir / "vault"
aww.settings.CONFIG_FILE = test_dir / "config.toml"


def test_invalid_vault():
    """Test that an invalid vault raises a ValueError."""
    with pytest.raises(ValueError):
        Vault("invalid_path")
    with pytest.raises(ValueError):
        Vault(".")


def test_valid_vault():
    v = Vault(test_vault_dir)
    assert v.path.name == "vault"


def test_valid_vault_default(mocker):
    v = Vault()
    assert v.path.name == "vault"


def test_pages():
    v = Vault(test_vault_dir)
    pages = v.pages()
    assert len(pages) == 3
    assert pages["index"].name == "index"
    assert pages["2025-03-30"].name == "2025-03-30"
    assert pages["2025-04-01"].name == "2025-04-01"


def test_journal():
    v = Vault(test_vault_dir)
    journal = v.journal()
    assert len(journal) == 2
    assert datetime.date(2025, 3, 30) in journal
    assert datetime.date(2025, 4, 1) in journal


def test_journal_subrange():
    v = Vault(test_vault_dir)
    journal = v.journal()
    assert len(journal) == 2
    subrange = journal.subrange(datetime.date(2025, 3, 1), datetime.date(2025, 3, 31))
    assert len(subrange) == 1
    assert datetime.date(2025, 3, 30) in subrange
    assert datetime.date(2025, 4, 1) not in subrange


def test_frontmatter():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-03-30"]
    assert page.frontmatter() == {"stress": 4}


def test_file_times():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-03-30"]
    assert page.created_time is not None
    assert page.modified_time is not None
    assert page.access_time is not None


def test_markdown():
    v = Vault(test_vault_dir)
    page = v.pages()["index"]
    assert (
        page.content()
        == "# Obsidian Test Vault\n\nJust a simple page.\n\n---\n\nThis page has no frontmatter.\n"
    )
    assert isinstance(page.content().__rich__(), rich.markdown.Markdown)


def test_markdown_parse():
    v = Vault(test_vault_dir)
    page = v.pages()["index"]
    parsed = page.content().parse()
    assert parsed == [
        {
            "type": "heading",
            "attrs": {"level": 1},
            "style": "atx",
            "children": [{"type": "text", "raw": "Obsidian Test Vault"}],
        },
        {"type": "blank_line"},
        {
            "type": "paragraph",
            "children": [{"type": "text", "raw": "Just a simple page."}],
        },
        {"type": "blank_line"},
        {"type": "thematic_break"},
        {"type": "blank_line"},
        {
            "type": "paragraph",
            "children": [{"type": "text", "raw": "This page has no frontmatter."}],
        },
    ]


def test_tasks():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-03-30"]
    tasks = page.tasks()
    if len(tasks) != 3:
        rich.print(page.content().parse())
    assert len(tasks) == 3
    assert tasks[0].name == "task 1"
    assert not tasks[0].done
    assert tasks[1].name == "task 2"
    assert tasks[1].done
    assert tasks[2].name == "task 3"
    assert tasks[2].done
    assert tasks[2].created == datetime.date(2025, 4, 3)
    assert tasks[2].due == datetime.date(2025, 4, 6)
    assert tasks[2].started == datetime.date(2025, 4, 4)
    assert tasks[2].scheduled == datetime.date(2025, 4, 3)
    assert tasks[2].completed == datetime.date(2025, 4, 4)
    assert tasks[2].recurrence == "every day when done"


def test_events():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-03-30"]
    events = page.events()
    if len(events) != 3:
        rich.print(page.content().parse())
    assert len(events) == 3
    assert events[0].name == "wake up"
    assert events[0].time == datetime.datetime(2025, 3, 30, 6, 15)
    assert events[1].name == "breakfast & shower"
    assert events[1].time == datetime.datetime(2025, 3, 30, 6, 30)
    assert events[0].duration == datetime.timedelta(minutes=15)
    assert events[2].name == "yoga"
    assert events[2].time == datetime.datetime(2025, 3, 30, 7, 0)
    assert events[1].duration == datetime.timedelta(minutes=30)
    assert events[2].duration is None


def test_events_2025_04_01():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-04-01"]
    events = page.events()
    if len(events) != 3:
        rich.print(page.content().parse())
    assert len(events) == 3
    assert events[0].name == "woke up"
    assert events[0].time == datetime.datetime(2025, 4, 1, 6, 4)
    assert events[0].duration == datetime.timedelta(minutes=56)
    assert events[1].name == "#aww did some personal development"
    assert events[1].tags == ["aww"]
    assert events[1].time == datetime.datetime(2025, 4, 1, 7, 0)
    assert events[1].duration == datetime.timedelta(hours=1, minutes=30)
    assert events[2].name == "#work"
    assert events[2].tags == ["work"]
    assert events[2].time == datetime.datetime(2025, 4, 1, 8, 30)
    assert events[2].duration == datetime.timedelta(hours=1)


def test_tags():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-04-01"]
    tags = page.tags()
    try:
        assert tags == [
            "tag1",
            "tag2",
            "tag3/with-parts",
            "aww",
            "work",
            "work",
            "work",
            "create/write/blog",
        ]
    except:
        rich.print(page.content().parse())
        raise
