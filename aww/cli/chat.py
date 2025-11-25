import click

from aww.chat import get_chat_agent
from aww.cli import main


@main.command(name="chat")
@click.pass_context
def chat(ctx):
    """Interactive chat with LLM access to the user's vault."""
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    agent = get_chat_agent(llm_model, vault)

    agent.to_cli_sync(prog_name="aww", deps=vault)
