from datetime import date, time
from pathlib import Path

import pandas as pd

import aww
from aww import obsidian
from aww.obsidian import TASK_RE, Level

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
    assert events_with_end_time.index.to_list() == [15, 16, 17]
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


def test_page_task_re():
    assert TASK_RE.match("- [x] task").groups() == ("x", "task")
    assert TASK_RE.match(" - [ ] task ➕ 2025-04-03").groups() == (
        " ",
        "task ➕ 2025-04-03",
    )


def test_page_tasks():
    page = obsidian.Page(test_vault_path / "journal/2025/03/2025-03-30.md", Level.daily)
    tasks = page.tasks()
    assert len(tasks) == 3
    assert tasks["status"].to_list() == [" ", "x", "x"]
    assert tasks["description"].to_list() == [
        "task 1",
        "task 2",
        "task 3 🔁 every day when done ➕ 2025-04-03 🛫 2025-04-04 ⏳ 2025-04-03 📅 2025-04-06  ✅ 2025-04-04",
    ]
    assert tasks.index.to_list() == [16, 17, 18]


def test_page_feedback():
    feedback_file = test_vault_path / "journal/2025/04/2025-04-02.md"
    feedback_file.write_text(
        "---\nfeedback_score: 8\n---\n# 2025-04-02\n\nContext line 1\nContext line 2\nContext line 3\n#feedback This is a feedback comment\nSome content\n#feedback Another feedback comment\nMore content\n#feedback    Whitespace handling\n"
    )
    try:
        page = obsidian.Page(feedback_file, Level.daily)
        feedback = page.feedback()
        assert len(feedback) == 3
        assert feedback[0] == {
            "comment": "This is a feedback comment",
            "context": "Context line 1\nContext line 2\nContext line 3",
        }
        assert feedback[1]["comment"] == "Another feedback comment"
        assert feedback[2]["comment"] == "Whitespace handling"

        assert page.feedback_score() == 8
    finally:
        if feedback_file.exists():
            feedback_file.unlink()


def test_page_tags():
    page = obsidian.Page(
        test_vault_path / "journal/2025/04/2025-04-01.md", Level.daily
    )
    tags = page.tags()
    assert "tag1" in tags
    assert "tag2" in tags
    assert "tag3/with-parts" in tags
    assert "aww" in tags
    assert "work" in tags
    assert "create/write/blog" in tags
    assert len(tags) == 6


def test_page_tags_frontmatter():
    temp_file = test_vault_path / "temp_tags.md"
    temp_file.write_text("---\ntags: fm-tag1, fm-tag2\n---\n# Content #content-tag\n")
    try:
        page = obsidian.Page(temp_file, None)
        tags = page.tags()
        assert tags == {"fm-tag1", "fm-tag2", "content-tag"}
    finally:
        if temp_file.exists():
            temp_file.unlink()
