import click
from pathlib import Path
import rich
from pydantic_ai import Agent
import asyncio
from aww.cli import main
from aww.rag import Index


@main.command()
@click.argument("query")
@click.option("--rag", is_flag=True, default=False, help="Use RAG for searching.")
@click.option(
    "--embedding-model-provider",
    type=str,
    default="sentence-transformers",
    help="The embedding model provider.",
)
@click.option(
    "--embedding-model-name",
    type=str,
    default="all-mpnet-base-v2",
    help="The embedding model name.",
)
@click.option(
    "-a", "--ask", is_flag=True, default=False, help="Ask LLM to compose the output."
)
@click.pass_context
def search(ctx, query, rag, embedding_model_provider, embedding_model_name, ask):
    """Searches the RAG index."""

    settings = ctx.obj["settings"]
    db_path = Path(settings.data_path) / "index"

    idx = Index(db_path, embedding_model_provider, embedding_model_name)
    idx.open_table()
    results = idx.search(query, rag=rag)

    rich.print(results[["id"]])

    if ask:
        llm_model = ctx.obj["llm_model"]
        ask_agent = Agent(model=llm_model, system_prompt=query)
        ask_result = asyncio.run(ask_agent.run([c for c in results["content"]]))

        rich.print(ask_result.output)
