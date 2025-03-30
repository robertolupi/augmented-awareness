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
    assert len(pages) == 2
    assert pages["index"].name == "index"
    assert pages["2025-03-30"].name == "2025-03-30"


def test_journal():
    v = Vault(test_vault_dir)
    journal = v.journal()
    assert len(journal) == 1
    assert datetime.date(2025, 3, 30) in journal


def test_frontmatter():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-03-30"]
    assert page.frontmatter() == {"stress": 4}


def test_markdown():
    v = Vault(test_vault_dir)
    page = v.pages()["index"]
    assert page.content() == "# Obsidian Test Vault\n\nJust a simple page.\n\n---\n\nThis page has no frontmatter.\n"
    assert isinstance(page.content().__rich__(), rich.markdown.Markdown)


def test_markdown_parse():
    v = Vault(test_vault_dir)
    page = v.pages()["index"]
    parsed = page.content().parse()
    assert parsed == [
        {
            'type': 'heading',
            'attrs': {'level': 1},
            'style': 'atx',
            'children': [{'type': 'text', 'raw': 'Obsidian Test Vault'}]
        },
        {'type': 'blank_line'},
        {
            'type': 'paragraph',
            'children': [{'type': 'text', 'raw': 'Just a simple page.'}]
        },
        {'type': 'blank_line'},
        {'type': 'thematic_break'},
        {'type': 'blank_line'},
        {
            'type': 'paragraph',
            'children': [{'type': 'text', 'raw': 'This page has no frontmatter.'}]
        }
    ]

def test_tasks():
    v = Vault(test_vault_dir)
    page = v.pages()["2025-03-30"]    
    tasks = page.tasks()
    if len(tasks) != 2:
        rich.print(page.content().parse())
        assert False
    assert tasks[0].name == 'task 1'
    assert not tasks[0].done
    assert tasks[1].name == 'task 2'
    assert tasks[1].done