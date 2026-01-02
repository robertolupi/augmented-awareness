import os

import click

from aww.chat import get_chat_agent
from aww.cli import main
from aww.deps import ChatDeps
from aww.rag import Index


@main.command(name="chat")
@click.pass_context
def chat(ctx):
    """Interactive chat with LLM access to the user's vault."""
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    settings = ctx.obj["settings"]

    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    index = Index.from_settings(settings)
    deps = ChatDeps(vault=vault, index=index)

    agent = get_chat_agent(llm_model, vault)

    agent.to_cli_sync(prog_name="aww", deps=deps)
