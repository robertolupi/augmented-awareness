import asyncio

import click
import rich
from pydantic_ai import Agent
from rich.markdown import Markdown

from aww.cli import main
from aww.rag import Index


@main.command()
@click.argument("query")
@click.option("--rag", is_flag=True, default=False, help="Use RAG for searching.")
@click.option(
    "-a", "--ask", default=None, help="Ask LLM to compose the output.",
    type=str,
)
@click.option("--output-file", type=click.Path(), help="File to write the output to.")
@click.option(
    "--plain-text",
    is_flag=True,
    default=False,
    help="Output plain text instead of markdown.",
)
@click.pass_context
def search(
    ctx,
    query,
    rag,
    ask,
    output_file,
    plain_text,
):
    """Searches the RAG index."""

    settings = ctx.obj["settings"]

    idx = Index.from_settings(settings)
    idx.open_table()
    results = idx.search(query, rag=rag)

    rich.print(results[["id"]])

    if ask:
        llm_model = ctx.obj["llm_model"]
        ask_agent = Agent(model=llm_model, system_prompt=ask)
        ask_result = asyncio.run(ask_agent.run([c for c in results["text"]]))

        output_content = ask_result.output
        if output_file:
            with open(output_file, "w") as f:
                f.write(output_content)
            print(f"Output written to {output_file}")
        if plain_text:
            print(output_content)
        else:
            rich.print(Markdown(output_content))
