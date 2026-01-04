import datetime
from pathlib import Path
import pytest
from aww.obsidian import Vault, Level, Page

@pytest.fixture
def temp_vault_dir(tmp_path):
    journal = tmp_path / "journal"
    journal.mkdir()
    retros = tmp_path / "retrospectives"
    retros.mkdir()
    return tmp_path

def test_iso_year_weekly_path(temp_vault_dir):
    v = Vault(temp_vault_dir, "journal", "retrospectives")
    # 2025-12-29 is Monday of W01 2026
    d = datetime.date(2025, 12, 29)
    p = v.page(d, Level.weekly)
    
    # Expected path uses 2026 for both directory and filename
    expected_rel_path = "journal/2026/weeks/2026-W01.md"
    assert str(p.path).endswith(expected_rel_path)

def test_page_section_extraction(tmp_path):
    test_file = tmp_path / "test_note.md"
    test_file.write_text("""# Daily Note

## Morning Routine
- Coffee
- Meditation

## Weekly Goals
- Finish the project
- Exercise 3 times

### Subgoals
- Subgoal 1

## Afternoon
Work hard.
""")
    
    p = Page(test_file)
    
    # Test extraction
    goals = p.section("Weekly Goals")
    expected_goals = "- Finish the project\n- Exercise 3 times\n\n### Subgoals\n- Subgoal 1"
    assert goals == expected_goals

    # Test case sensitivity
    assert p.section("weekly goals") == goals
    
    # Test non-existent section
    assert p.section("Non-existent") is None

def test_page_section_boundary(tmp_path):
    test_file = tmp_path / "test_note.md"
    test_file.write_text("""# Header 1
Content 1
## Header 2
Content 2
### Header 3
Content 3
## Header 4
Content 4
""")
    p = Page(test_file)
    
    # Section Header 2 should include Header 3 but stop at Header 4 (same level)
    section2 = p.section("Header 2")
    assert "Content 2" in section2
    assert "### Header 3" in section2
    assert "Content 3" in section2
    assert "## Header 4" not in section2
    
    # Section Header 3 should stop at Header 4 (higher level)
    section3 = p.section("Header 3")
    assert "Content 3" in section3
    assert "## Header 4" not in section3
