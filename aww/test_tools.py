import datetime
from unittest.mock import MagicMock, patch
import pytest
from pydantic_ai import RunContext

from aww.obsidian import Level, Page, Vault
from aww.tools import (
    datetime_tool,
    read_journal_tool,
    read_pages_tool,
    read_retro_tool,
    read_tasks_tool,
    remember_tool,
    search_tool,
)
import pandas as pd


@pytest.fixture
def mock_vault():
    return MagicMock(spec=Vault)


@pytest.fixture
def mock_ctx(mock_vault):
    ctx = MagicMock(spec=RunContext)
    ctx.deps = mock_vault
    return ctx


def test_datetime_tool(mock_ctx):
    result = datetime_tool(mock_ctx)
    assert "Now is" in result
    assert "The pages relevant to today are:" in result


def test_read_journal_tool(mock_ctx):
    mock_page = MagicMock(spec=Page)
    mock_page.name = "2023-10-01"
    mock_page.content.return_value = "Journal content"
    
    mock_retro_page = MagicMock(spec=Page)
    mock_retro_page.name = "r2023-10-01"
    mock_retro_page.content.return_value = "Retro content"
    
    mock_ctx.deps.page.return_value = mock_page
    mock_ctx.deps.retrospective_page.return_value = mock_retro_page
    
    result = read_journal_tool(mock_ctx)
    
    assert "The user journal for the past week is as follows:" in result
    assert "# 2023-10-01" in result
    assert "Journal content" in result
    assert "# r2023-10-01" in result
    assert "Retro content" in result


def test_read_pages_tool(mock_ctx):
    mock_page = MagicMock(spec=Page)
    mock_page.name = "MyPage"
    mock_page.content.return_value = "Page content"
    
    mock_ctx.deps.page_by_name.side_effect = [mock_page, ValueError("Not found")]
    
    result = read_pages_tool(mock_ctx, ["MyPage", "MissingPage"])
    
    assert "# MyPage" in result
    assert "Page content" in result
    assert "Page 'MissingPage' not found." in result


def test_read_retro_tool(mock_ctx):
    mock_page = MagicMock(spec=Page)
    mock_page.name = "rToday"
    mock_page.content.return_value = "Retro content"
    
    mock_ctx.deps.retrospective_page.return_value = mock_page
    
    result = read_retro_tool(mock_ctx)
    
    assert "# rToday" in result
    assert "Retro content" in result


def test_read_tasks_tool(mock_ctx):
    mock_page = MagicMock(spec=Page)
    # Mock tasks dataframe
    df = pd.DataFrame({
        "status": [" ", "x"],
        "description": ["Task 1", "Task 2"]
    })
    mock_page.tasks.return_value = df
    
    mock_ctx.deps.page.return_value = mock_page
    
    # Test default (exclude done)
    result = read_tasks_tool(mock_ctx, start="2023-01-01", end="2023-01-01")
    assert "- [ ] Task 1" in result
    assert "- [x] Task 2" not in result
    
    # Test include done
    result = read_tasks_tool(mock_ctx, start="2023-01-01", end="2023-01-01", include_done="true")
    assert "- [ ] Task 1" in result
    assert "- [x] Task 2" in result


def test_search_tool(mock_ctx):
    mock_page1 = MagicMock(spec=Page)
    mock_page1.name = "FoundPage"
    mock_page1.content.return_value = "Content 1"
    
    mock_page2 = MagicMock(spec=Page)
    mock_page2.name = "OtherPage"
    
    mock_ctx.deps.walk.return_value = [mock_page1, mock_page2]
    
    result = search_tool(mock_ctx, "Found")
    
    assert "# FoundPage" in result
    assert "Content 1" in result
    assert "OtherPage" not in result


def test_remember_tool(mock_ctx):
    mock_page = MagicMock(spec=Page)
    mock_page.path = "dummy_path"
    mock_ctx.deps.page_by_name.return_value = mock_page
    
    with patch("builtins.open", new_callable=MagicMock) as mock_open:
        result = remember_tool(mock_ctx, "Remember this")
        
        assert "Fact remembered successfully!" in result
        mock_open.assert_called_with("dummy_path", "a")
        mock_open.return_value.__enter__.return_value.write.assert_called_with("\nRemember this")
