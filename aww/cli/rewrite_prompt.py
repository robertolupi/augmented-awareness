import asyncio
import datetime
import textwrap
from pathlib import Path

import click
import rich
from rich.markdown import Markdown

import aww
import aww.retro, aww.retro_gen
from aww import retro
from aww.cli import main
from aww.config import create_model
from aww.obsidian import Level
from pydantic_ai import Agent


@main.command()
@click.option("--critique-model", type=str, default="local")
@click.option(
    "-d", "--date", type=click.DateTime(), default=datetime.date.today().isoformat()
)
@click.option(
    "-c",
    "--context",
    type=click.Choice(Level, case_sensitive=False),
    multiple=True,
    help="Context levels for retrospective",
    default=[Level.daily, Level.weekly, Level.monthly, Level.yearly],
)
@click.argument("level", type=click.Choice(Level, case_sensitive=False))
@click.option(
    "-y",
    "--yesterday",
    is_flag=True,
    default=False,
    help="Switch to previous date (only for daily level)",
)
@click.pass_context
def rewrite_prompt(
    ctx,
    critique_model: str,
    date,
    yesterday,
    context,
    level,
):
    vault = ctx.obj["vault"]
    llm_model = ctx.obj["llm_model"]
    if yesterday:
        date = date - datetime.timedelta(days=1)

    sel = retro.Selection(vault, date, level)
    node = sel.root
    sources = [n for n in node.sources if n.level in context]
    if node.level in context:
        sources.insert(0, node)
    content = [s.retro_page.content() for s in sources if s.retro_page]
    if level == Level.daily:
        page_content = asyncio.run(aww.retro_gen.page_content(node))
        content.insert(0, page_content)

    model = create_model(critique_model)
    critique_agent = Agent(model=model, output_type=str)

    @critique_agent.system_prompt
    def critique():
        return textwrap.dedent(
            """
        You are an expert at writing LLM prompts. You will receive:
        1) the prompt
        2) the output
        3) a series of input messages
        Your job is to write a revised prompt that is more performant.
        Write only the revised prompt in full, in markdown format.
        """
        )

    prompt_file = Path(aww.__file__).parent / "retro" / f"{level.value}.md"
    prompt = prompt_file.read_text()

    gen_agent = Agent(model=llm_model, system_prompt=prompt)

    async def do_critique():
        gen_result = await gen_agent.run(user_prompt=content)
        gen_output = gen_result.output
        critique_result = await critique_agent.run(
            user_prompt=[prompt, gen_output] + content
        )
        return critique_result.output

    result = asyncio.run(do_critique())
    rich.print(Markdown(result))
    prompt_file.write_text(result)
