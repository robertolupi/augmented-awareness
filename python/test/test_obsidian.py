import datetime
import pathlib

import pytest
import rich
import rich.markdown

from aww.observe.obsidian import Vault

test_dir = pathlib.Path(__file__).parent
test_vault_dir = test_dir / "vault"


def test_invalid_vault():
    """Test that an invalid vault raises a ValueError."""
    with pytest.raises(ValueError):
        Vault("invalid_path")
    with pytest.raises(ValueError):
        Vault(".")


def test_valid_vault():
    v = Vault(test_vault_dir)
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


def test_frontmatter():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-03-30"]
    assert page.frontmatter() == {"stress": 4}


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
    assert tasks[0].name == "task 1"
    assert not tasks[0].done
    assert tasks[1].name == "task 2"
    assert tasks[1].done
    assert tasks[2].name == "task 3"
    assert not tasks[2].done
    assert tasks[2].created == datetime.date(2025, 4, 3)
    assert tasks[2].due == datetime.date(2025, 4, 6)
    assert tasks[2].started == datetime.date(2025, 4, 4)
    assert tasks[2].scheduled == datetime.date(2025, 4, 3)
    assert tasks[2].recurrence == "every day when done"
    if len(tasks) != 3:
        rich.print(page.content().parse())
        assert False


def test_events():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-03-30"]
    events = page.events()
    if len(events) != 3:
        rich.print(page.content().parse())
        assert False
    assert events[0].name == "wake up"
    assert events[0].time == datetime.datetime(2025, 3, 30, 6, 15)
    assert events[1].name == "breakfast & shower"
    assert events[1].time == datetime.datetime(2025, 3, 30, 6, 30)
    assert events[0].duration == datetime.timedelta(minutes=15)
    assert events[2].name == "yoga"
    assert events[2].time == datetime.datetime(2025, 3, 30, 7, 0)
    assert events[1].duration == datetime.timedelta(minutes=30)
    assert events[2].duration is None


def test_events_tags():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-04-01"]
    events = page.events()
    if len(events) != 3:
        rich.print(page.content().parse())
    assert events[0].name == "woke up"
    assert events[0].time == datetime.datetime(2025, 4, 1, 6, 4)
    assert events[1].name == "#aww did some work"
    assert events[1].tags == ["aww"]
    assert events[1].time == datetime.datetime(2025, 4, 1, 7, 0)
    assert events[2].name == "#work"
    assert events[2].tags == ["work"]
    assert events[2].time == datetime.datetime(2025, 4, 1, 8, 30)


def test_tags():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-04-01"]
    tags = page.tags()
    try:
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3/with-parts" in tags
        assert "aww" in tags
        assert "work" in tags
        assert len(tags) == 5
    except:
        rich.print(page.content().parse())
        raise
