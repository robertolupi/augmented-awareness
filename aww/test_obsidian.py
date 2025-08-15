from datetime import date, time
from pathlib import Path

import pandas as pd

import aww
from aww import obsidian
from aww.obsidian import Level

test_vault_path = (Path(aww.__file__).parent.parent / "test_vault").absolute()


def test_vault():
    vault = obsidian.Vault(test_vault_path, "journal", "retrospectives")
    assert vault.path == test_vault_path
    assert vault.journal_dir == "journal"
    assert vault.retrospectives_dir == "retrospectives"
    assert vault.path.exists()


def test_daily_page():
    vault = obsidian.Vault(test_vault_path, "journal", "retrospectives")
    d = date(2025, 3, 30)
    page = vault.page(d, Level.daily)
    assert (
        page.path.absolute()
        == (test_vault_path / "journal/2025/03/2025-03-30.md").absolute()
    )
    assert page.path.exists()
    assert page


def test_page():
    page1 = obsidian.Page(
        test_vault_path / "journal/2025/03/2025-03-30.md", Level.daily
    )
    page2 = obsidian.Page(
        test_vault_path / "journal/2025/04/2025-04-01.md", Level.daily
    )
    assert page1 != page2
    assert hash(page1) != hash(page2)

    assert page1.frontmatter() == {"stress": 4}
    assert page2.frontmatter() == {"stress": 5}


def test_index_page():
    page = obsidian.Page(test_vault_path / "index.md", None)
    assert not page.frontmatter()


def test_page_events():
    page_simple = obsidian.Page(
        test_vault_path / "journal/2025/03/2025-03-30.md", Level.daily
    )
    events_simple = page_simple.events()
    assert len(events_simple) == 3
    assert events_simple["start"].to_list() == [time(6, 15), time(6, 30), time(7, 0)]
    assert events_simple["description"].to_list() == [
        "wake up",
        "breakfast & shower",
        "yoga",
    ]
    assert events_simple["end"].isna().all()

    page_with_end_time = obsidian.Page(
        test_vault_path / "journal/2025/04/2025-04-01.md", Level.daily
    )
    events_with_end_time = page_with_end_time.events()
    assert len(events_with_end_time) == 3
    assert events_with_end_time["start"].to_list() == [
        time(6, 4),
        time(7, 0),
        time(8, 30),
    ]
    assert events_with_end_time["description"].to_list() == [
        "woke up",
        "#aww did some personal development",
        "#work",
    ]
    assert pd.isna(events_with_end_time["end"].iloc[0])
    assert pd.isna(events_with_end_time["end"].iloc[1])
    assert events_with_end_time["end"].iloc[2] == time(9, 30)