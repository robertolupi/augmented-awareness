import datetime
import re
from typing import List

from pydantic_ai import RunContext

from aww.deps import ChatDeps
from aww.obsidian import Level


def datetime_tool(ctx: RunContext[ChatDeps]) -> str:
    """
    Get the date and time as of today.
    """
    now = datetime.datetime.now()
    output = []
    output.append(f"Now is {now.strftime('%A, %Y-%m-%d %H:%M:%S')}")
    output.append("The pages relevant to today are:")
    output.append(f" - Year: [[Y{now.year}]]")
    output.append(f" - Month: [[{now.strftime('%Y-%m')}]]")
    output.append(f" - Day: [[{now.strftime('%Y-%m-%d')}]]")
    year, week, _ = now.isocalendar()
    output.append(f" - Week: [[{year}-W{week:02d}]]")
    return "\n".join(output)


def read_journal_tool(ctx: RunContext[ChatDeps]) -> str:
    """
    Read journal for the past week, up to and including today.
    """
    vault = ctx.deps.vault
    today = datetime.date.today()
    output = []
    
    # Add current datetime info first
    output.append(datetime_tool(ctx))
    output.append("\nThe user journal for the past week is as follows:\n")

    for i in range(7):
        d = today - datetime.timedelta(days=6 - i)
        
        # Daily page
        page = vault.page(d, Level.daily)
        if page:
            output.append(f"# {page.name}\n{page.content()}\n")
        
        # Daily retro page
        retro_page = vault.retrospective_page(d, Level.daily)
        if retro_page:
            output.append(f"# {retro_page.name}\n{retro_page.content()}\n")

    return "\n".join(output)


def read_pages_tool(ctx: RunContext[ChatDeps], pages: List[str]) -> str:
    """
    Read one or more pages from the vault, and return their content in markdown format.
    
    Args:
        pages: Names of pages to read, e.g. 2023-10-01 or [[2023-10-01]].
    """
    vault = ctx.deps.vault
    output = []
    
    for name in pages:
        # Clean up brackets if present
        clean_name = name.replace("[[", "").replace("]]", "")
        try:
            page = vault.page_by_name(clean_name)
            output.append(f"# {page.name}\n{page.content()}\n")
        except ValueError:
            output.append(f"Page '{clean_name}' not found.\n")
            
    return "\n".join(output)


def read_retro_tool(ctx: RunContext[ChatDeps]) -> str:
    """
    Read yearly/monthly/weekly/daily retrospectives for the given date (today).
    """
    vault = ctx.deps.vault
    today = datetime.date.today()
    output = []
    
    levels = [Level.daily, Level.weekly, Level.monthly, Level.yearly]
    
    for level in levels:
        page = vault.retrospective_page(today, level)
        if page:
            output.append(f"# {page.name}\n{page.content()}\n")
            
    if not output:
        return "No retrospectives found for today."
        
    return "\n".join(output)


def read_tasks_tool(
    ctx: RunContext[ChatDeps], 
    start: str = None, 
    end: str = None, 
    include_done: str = "false"
) -> str:
    """
    Read tasks for a given date range.
    
    Args:
        start: Start date (YYYY-MM-DD). Defaults to one week ago.
        end: End date (YYYY-MM-DD). Defaults to today.
        include_done: Whether to include completed tasks ("true"/"false"). Defaults to "false".
    """
    vault = ctx.deps.vault
    today = datetime.date.today()
    
    if start:
        start_date = datetime.date.fromisoformat(start)
    else:
        start_date = today - datetime.timedelta(days=6)
        
    if end:
        end_date = datetime.date.fromisoformat(end)
    else:
        end_date = today
        
    include_done_bool = include_done.lower() == "true"
    
    output = []
    output.append(f"# Tasks from {start_date} to {end_date}\n")
    
    found_tasks = False
    
    # Iterate through dates
    current = start_date
    while current <= end_date:
        page = vault.page(current, Level.daily)
        if page:
            tasks_df = page.tasks()
            if not tasks_df.empty:
                for _, row in tasks_df.iterrows():
                    status = row['status']
                    description = row['description']
                    
                    # Check if task is done (x or X usually means done in Obsidian)
                    is_done = status.lower() == 'x'
                    
                    if include_done_bool or not is_done:
                        output.append(f"- [{status}] {description}")
                        found_tasks = True
        
        current += datetime.timedelta(days=1)
        
    if not found_tasks:
        output.append("No tasks found in the specified date range.")
        
    return "\n".join(output)


def remember_tool(ctx: RunContext[ChatDeps], fact: str) -> str:
    """
    Remember a fact or piece of information. Facts will be stored in a page called 'aww-scratchpad' in the vault.
    
    Args:
        fact: The fact or information to remember, in markdown format.
    """
    vault = ctx.deps.vault
    try:
        page = vault.page_by_name("aww-scratchpad")
    except ValueError:
        return "Error: 'aww-scratchpad' page not found."

    # Append to file
    with open(page.path, "a") as f:
        f.write(f"\n{fact}")
        
    return "Fact remembered successfully!"


def search_tool(ctx: RunContext[ChatDeps], query: str) -> str:
    """
    Search for pages in the vault using RAG (Retrieval Augmented Generation).
    
    Args:
        query: The query to search for.
    """
    if not ctx.deps.index:
        return "Search is not available (index not initialized)."
        
    try:
        # Open table if not already open
        if ctx.deps.index.tbl is None:
            ctx.deps.index.open_table()
            
        if ctx.deps.index.tbl is None:
             return "Search index not found. Please run 'aww index' first."

        results_df = ctx.deps.index.search(query)
        
        if results_df.empty:
            return "No pages found matching your search query."
            
        output = []
        for _, row in results_df.iterrows():
            output.append(f"# {row['id']}\n{row['text']}\n")
            
        return "\n".join(output)
        
    except Exception as e:
        return f"Error performing search: {str(e)}"
