import click
from pathlib import Path
import rich
from rich.markdown import Markdown
from pydantic_ai import Agent
import asyncio
from aww.cli import main
from aww.rag import Index


@main.command()
@click.argument("query")
@click.option("--rag", is_flag=True, default=False, help="Use RAG for searching.")
@click.option(
    "-a", "--ask", is_flag=True, default=False, help="Ask LLM to compose the output."
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
    db_path = Path(settings.data_path) / "index"

    idx = Index(
        db_path,
        settings.rag.provider,
        settings.rag.model_name,
    )
    idx.open_table()
    results = idx.search(query, rag=rag)

    rich.print(results[["id"]])

    if ask:
        llm_model = ctx.obj["llm_model"]
        ask_agent = Agent(model=llm_model, system_prompt=query)
        ask_result = asyncio.run(ask_agent.run([c for c in results["content"]]))

        output_content = ask_result.output
        if output_file:
            with open(output_file, "w") as f:
                f.write(output_content)
            print(f"Output written to {output_file}")
        if plain_text:
            print(output_content)
        else:
            rich.print(Markdown(output_content))
