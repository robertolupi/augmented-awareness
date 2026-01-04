import datetime
from unittest.mock import MagicMock
import pytest
from aww.cli.motd import get_motd_context
from aww.obsidian import Vault, Page, Level

@pytest.fixture
def mock_vault():
    vault = MagicMock(spec=Vault)
    return vault

def test_get_motd_context_with_metrics(mock_vault):
    # Mock daily note with frontmatter
    daily_note = MagicMock(spec=Page)
    daily_note.content.return_value = "Daily note content"
    daily_note.frontmatter.return_value = {
        "stress": 5,
        "mood": "Happy",
        "sleep_score": 85
    }
    
    # Configure vault to return this note
    mock_vault.page.return_value = daily_note
    
    # Mock other pages to return None or empty to simplify
    mock_vault.retrospective_page.return_value = None
    mock_vault.page_by_name.return_value = None

    context = get_motd_context(mock_vault, daily=True, yesterday=False, weekly=False, memory=False)
    
    # Join context to search for strings
    full_context = "\n".join(context)
    
    assert "=== DAILY NOTES ===" in full_context
    assert "Daily note content" in full_context
    assert "=== TODAY'S METRICS ===" in full_context
    assert "Stress level 5 of 10." in full_context
    assert "Mood: Happy" in full_context
    assert "Sleep Score: 85 of 100." in full_context

def test_get_motd_context_no_metrics(mock_vault):
    # Mock daily note without frontmatter
    daily_note = MagicMock(spec=Page)
    daily_note.content.return_value = "Daily note content"
    daily_note.frontmatter.return_value = {}
    
    mock_vault.page.return_value = daily_note
    mock_vault.retrospective_page.return_value = None
    mock_vault.page_by_name.return_value = None

    context = get_motd_context(mock_vault, daily=True, yesterday=False, weekly=False, memory=False)
    
    full_context = "\n".join(context)
    
    assert "=== DAILY NOTES ===" in full_context
    assert "=== TODAY'S METRICS ===" not in full_context

def test_get_motd_context_with_weekly_goals(mock_vault):
    # Mock weekly retrospective
    weekly_retro = MagicMock(spec=Page)
    weekly_retro.content.return_value = "Weekly retro content"
    
    # Mock weekly journal note with Weekly Goals section
    weekly_note = MagicMock(spec=Page)
    weekly_note.section.side_effect = lambda title: "Goal 1\nGoal 2" if title == "Weekly Goals" else None
    
    # Configure vault to return these pages
    # mock_vault.page(d, Level.weekly) -> weekly_note
    # mock_vault.retrospective_page(d, Level.weekly) -> weekly_retro
    def side_effect(d, level):
        if level == Level.weekly:
            if mock_vault.retrospective_page.called_with(d, level):
                return weekly_retro
            return weekly_note
        return None

    mock_vault.retrospective_page.side_effect = lambda d, l: weekly_retro if l == Level.weekly else None
    mock_vault.page.side_effect = lambda d, l: weekly_note if l == Level.weekly else None
    mock_vault.page_by_name.return_value = None

    context = get_motd_context(mock_vault, daily=False, yesterday=False, weekly=True, memory=False)
    
    full_context = "\n".join(context)
    
    assert "=== WEEKLY RETROSPECTIVE ===" in full_context
    assert "Weekly retro content" in full_context
    assert "=== WEEKLY GOALS ===" in full_context
    assert "Goal 1\nGoal 2" in full_context
