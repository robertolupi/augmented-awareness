import textwrap
from typing import Any

import click
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio, CallToolFunc, ToolResult

from aww.cli import main
from aww.chat import get_chat_agent
from aww.prompts import select_prompt_template


@main.command(name="chat")
@click.pass_context
def chat(ctx):
    """Interactive chat with LLM access to the user's vault."""
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    agent = get_chat_agent(llm_model)

    @agent.system_prompt
    def system_prompt():
        return select_prompt_template(["chat.md"]).render()

    agent.to_cli_sync(prog_name="aww")
