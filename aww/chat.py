import datetime
import os
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models import Model


def is_executable(path: Path) -> bool:
    """Check if a path is executable."""
    return path.is_file() and os.access(path, os.X_OK)


def get_chat_agent(model: Model) -> Agent:
    toolsets = []

    journal = Path(__file__).parent.parent / "journal"
    if journal.exists() and is_executable(journal):
        journal_mcp = MCPServerStdio(
            str(journal.absolute()),
            args=["mcp"],
        )
        toolsets.append(journal_mcp)

    agent = Agent(model, toolsets=toolsets)

    @agent.tool_plain
    def current_date_time() -> datetime.datetime:
        """Get the current date and time, in the local timezone."""
        return datetime.datetime.now()

    return agent
