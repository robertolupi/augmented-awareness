import datetime
import os
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models import Model

from aww.obsidian import Page, Vault
from aww.prompts import select_prompt_template


def is_executable(path: Path) -> bool:
    """Check if a path is executable."""
    return path.is_file() and os.access(path, os.X_OK)


def get_chat_agent(model: Model, vault: Vault) -> Agent:
    toolsets = []

    journal = Path(__file__).parent.parent / "journal"
    if journal.exists() and is_executable(journal):
        journal_mcp = MCPServerStdio(
            str(journal.absolute()),
            args=["mcp"],
        )
        toolsets.append(journal_mcp)

    agent = Agent(model, toolsets=toolsets)

    scratchpad: Page | None = None
    for page in vault.walk():
        if page.name == "aww-scratchpad":
            scratchpad = page

    @agent.system_prompt
    def system_prompt():
        result = select_prompt_template(["chat.md"]).render(now=datetime.datetime.now())
        if scratchpad:
            result += (
                "The content of your memories in the [[aww-scratchpad]] page is:\n"
                + scratchpad.content()
            )
        return result

    return agent
