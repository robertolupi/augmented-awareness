import asyncio
import datetime
import hashlib
from typing import Any, Callable, List, Optional

import rich
from pydantic_ai import Agent
from pydantic_ai.models import Model
from rich.markdown import Markdown

from aww import retro, retro_gen
from aww.obsidian import Level, Vault


def ask_question(
    vault: Vault,
    llm_model: Model,
    date: datetime.date,
    level: Level,
    prompt: str,
    context_levels: List[Level],
    verbose: bool = False,
    recursive: bool = False,
    cache_policies: Optional[List[retro.CachePolicy]] = None,
    gather: Callable = asyncio.gather,
) -> str:
    """
    Core logic for the ask command.
    """
    sel = retro.Selection(vault, date, level)

    if recursive:
        # Generate a unique query ID based on the prompt/question
        query_id = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8]
        if verbose:
            rich.print(f"Recursive Query ID: {query_id}")

        # Save the query prompt to query.md in the query directory
        query_dir = vault.path / vault.queries_dir / query_id
        query_dir.mkdir(parents=True, exist_ok=True)
        (query_dir / "query.md").write_text(prompt)

        generator = retro_gen.RecursiveGenerator(
            model=llm_model,
            sel=sel,
            prompt_prefix="ask_",
            extra_vars={"question": prompt},
            get_target_page=lambda node: vault.query_page(query_id, node.dates.copy().pop() if node.dates else date, node.level),
        )
        
        # Use default cache policies if not provided
        final_cache_policies = cache_policies
        if final_cache_policies is None:
            final_cache_policies = [retro.NoRootCachePolicy(), retro.ModificationTimeCachePolicy()]

        result = asyncio.run(
            generator.run(
                context_levels=context_levels,
                cache_policies=final_cache_policies,
                gather=gather,
            )
        )
        return result.output if result else "No Result"

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
