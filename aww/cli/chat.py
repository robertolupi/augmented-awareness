import textwrap
from typing import Any

import click
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio, CallToolFunc, ToolResult

from aww.cli import main


async def process_tool_call(
    ctx: RunContext[int],
    call_tool: CallToolFunc,
    name: str,
    tool_args: dict[str, Any],
) -> ToolResult:
    """A tool call processor that passes along the deps."""
    print(f"Tool call {name}")
    return await call_tool(name, tool_args, {"deps": ctx.deps})


@main.command(name="chat")
@click.option("-j", "--journal_cmd", type=str, default="./journal")
@click.pass_context
def chat(ctx, journal_cmd):
    """Interactive chat with LLM access to the user's vault."""
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    server = MCPServerStdio(
        journal_cmd,
        args=["--vault", str(vault.path), "mcp"],
        process_tool_call=process_tool_call,
    )
    ask_agent = Agent(model=llm_model, toolsets=[server])

    @ask_agent.system_prompt
    def system_prompt():
        return textwrap.dedent(
            """You are a helpful holistic assistant. 
        Read the user retrospectives, weekly journal and pages as needed, then answer the user question.
        Call at most one tool at a time.
        """
        )

    ask_agent.to_cli_sync(prog_name="aww")
