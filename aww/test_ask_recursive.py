import datetime
import hashlib
from pydantic_ai.models.test import TestModel
from aww import retro, ask
from aww.obsidian import Level
from aww.test_retro import tmp_vault

def test_recursive_ask_logic(tmp_vault):
    """
    Test the recursive ask logic using a TestModel.
    Verifies that the recursive generator is called and query pages are created.
    """
    model = TestModel()
    
    date_val = datetime.date(2025, 4, 1)
    # Use weekly level for a smaller test
    level = Level.weekly
    prompt = "What did I do this week?"
    
    # Run ask_question in recursive mode
    # It internally handles the asyncio loop for the generator
    result = ask.ask_question(
        vault=tmp_vault,
        llm_model=model,
        date=date_val,
        level=level,
        prompt=prompt,
        context_levels=[Level.daily, Level.weekly],
        recursive=True,
        verbose=True
    )
    
    assert result is not None
    
    # Check if a query page was created for the root level
    query_id = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8]
    query_page = tmp_vault.query_page(query_id, date_val, Level.weekly)
    assert query_page.path.exists(), f"Query page {query_page.path} should exist"

    # Verify query.md creation
    query_dir = tmp_vault.path / tmp_vault.queries_dir / query_id
    assert (query_dir / "query.md").exists()
    assert (query_dir / "query.md").read_text() == prompt
    
    # Check if a daily query page was created for an existing journal entry
    # 2025-04-01 is known to exist in the test_vault
    daily_date = datetime.date(2025, 4, 1)
    daily_query_page = tmp_vault.query_page(query_id, daily_date, Level.daily)
    assert daily_query_page.path.exists(), f"Daily query page {daily_query_page.path} should exist"

def test_recursive_ask_caching(tmp_vault):
    """
    Test that recursive ask respects caching.
    """
    model = TestModel()
    date_val = datetime.date(2025, 4, 1)
    prompt = "Cached question?"
    query_id = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8]
    
    # Run once to populate cache
    ask.ask_question(
        vault=tmp_vault,
        llm_model=model,
        date=date_val,
        level=Level.daily,
        prompt=prompt,
        context_levels=[Level.daily],
        recursive=True
    )
    
    query_page = tmp_vault.query_page(query_id, date_val, Level.daily)
    assert query_page.path.exists()
    
    # Modify the cached file to include a specific marker
    content = query_page.path.read_text()
    with query_page.path.open("w") as f:
        f.write(content + "\n\nCACHED_MARKER")
        
    # Run again with empty cache policies so root cache is used
    result = ask.ask_question(
        vault=tmp_vault,
        llm_model=model,
        date=date_val,
        level=Level.daily,
        prompt=prompt,
        context_levels=[Level.daily],
        recursive=True,
        cache_policies=[]
    )
    
    assert "CACHED_MARKER" in result
