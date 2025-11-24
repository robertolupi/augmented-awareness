import datetime
from typing import List, Optional

import rich
from pydantic_ai import Agent
from pydantic_ai.models import Model
from rich.markdown import Markdown

from aww import retro
from aww.obsidian import Level, Vault


def ask_question(
    vault: Vault,
    llm_model: Model,
    date: datetime.date,
    level: Level,
    prompt: str,
    context_levels: List[Level],
    verbose: bool = False,
) -> str:
    """
    Core logic for the ask command.
    """
    sel = retro.Selection(vault, date, level)

    ask_agent = Agent(model=llm_model, system_prompt=prompt)

    node = sel.root
    sources = [n for n in node.sources if n.level in context_levels]
    if node.level in context_levels:
        sources.insert(0, node)
    sources = [s for s in sources if s.retro_page]
    
    if verbose:
        rich.print("Sources", [n.retro_page.name for n in sources])
        
    retros = [n.retro_page.content() for n in sources]

    result = ask_agent.run_sync(user_prompt=retros)
    return result.output
