import datetime
import os
from pathlib import Path

from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model

from aww.obsidian import Page, Vault
from aww.prompts import select_prompt_template


from aww.tools import (
    datetime_tool,
    read_journal_tool,
    read_pages_tool,
    read_retro_tool,
    read_tasks_tool,
    remember_tool,
    search_tool,
)


def is_executable(path: Path) -> bool:
    """Check if a path is executable."""
    return path.is_file() and os.access(path, os.X_OK)


def get_chat_agent(model: Model, vault: Vault) -> Agent[Vault]:
    agent = Agent(
        model,
        deps_type=Vault,
        tools=[
            datetime_tool,
            read_journal_tool,
            read_pages_tool,
            read_retro_tool,
            read_tasks_tool,
            remember_tool,
            search_tool,
        ],
    )

    scratchpad: Page | None = None
    try:
        scratchpad = vault.page_by_name("aww-scratchpad")
    except ValueError:
        pass

    @agent.system_prompt
    def system_prompt(ctx: RunContext[Vault]):
        result = select_prompt_template(["chat.md"]).render(now=datetime.datetime.now())
        if scratchpad:
            result += (
                "The content of your memories in the [[aww-scratchpad]] page is:\n"
                + scratchpad.content()
            )
        return result

    return agent
