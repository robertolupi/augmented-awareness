import asyncio
import datetime
import textwrap
from pathlib import Path
from typing import List, Optional

import rich
from pydantic_ai import Agent
from pydantic_ai.models import Model
from rich.markdown import Markdown

import aww
import aww.retro
import aww.retro_gen
from aww import retro
from aww.config import create_model
from aww.obsidian import Level, Vault


def optimize_prompt(
    critique_model_name: str,
    llm_model: Model,
    current_prompt: str,
    test_inputs: List[str],
    feedback: Optional[List[dict]] = None,
    scores: Optional[List[str]] = None,
) -> str:
    """
    Core logic for rewriting prompts based on critique and feedback.
    """
    model = create_model(critique_model_name)
    critique_agent = Agent(model=model, output_type=str)

    @critique_agent.system_prompt
    def critique():
        return textwrap.dedent(
            """
        You are an expert at writing LLM prompts. You will receive:
        1) the prompt
        2) the output
        3) a series of input messages
        4) a list of human feedback comments (optional)
        5) a list of feedback scores for the retrospectives (optional)
        Your job is to write a revised prompt that is more performant.
        If feedback is provided, you must incorporate it into the revised prompt.
        If feedback scores are provided, use them to understand which retrospectives were better received.
        Write only the revised prompt in full, in markdown format.
        """
        )

    gen_agent = Agent(model=llm_model, system_prompt=current_prompt)

    async def do_critique():
        # Generate output for the test inputs using the current prompt
        # For simplicity in this generalized version, we'll just use the first input
        # or concatenate them if appropriate. In the original logic, 'content' was a list of strings.
        # The gen_agent.run takes user_prompt which can be a string or list of content.
        gen_result = await gen_agent.run(user_prompt=test_inputs)
        gen_output = gen_result.output

        feedback_str = ""
        if feedback:
            feedback_str = "\n".join(
                [
                    f"Context:\n{f['context']}\nComment: {f['comment']}\n"
                    for f in feedback
                ]
            )

        user_prompt = [
            current_prompt,
            gen_output,
            f"Human Feedback:\n{feedback_str}",
        ]
        if scores:
            user_prompt.append(f"Retrospective Feedback Scores:\n{'\n'.join(scores)}")

        user_prompt.extend(test_inputs)

        critique_result = await critique_agent.run(user_prompt=user_prompt)
        return critique_result.output

    result = asyncio.run(do_critique())
    return result


def rewrite_prompt_logic(
    critique_model_name: str,
    llm_model: Model,
    vault: Vault,
    date: datetime.date,
    level: Level,
    context_levels: List[Level],
    current_prompt: str,
    external_feedback: Optional[List[str]] = None,
) -> str:
    """
    Logic for rewriting prompts based on critique and feedback.
    """
    sel = retro.Selection(vault, date, level)
    node = sel.root
    sources = [n for n in node.sources if n.level in context_levels]
    if node.level in context_levels:
        sources.insert(0, node)
    content = [s.retro_page.content() for s in sources if s.retro_page]
    feedback = []
    if external_feedback:
        feedback.extend(
            [{"comment": f, "context": "CLI Feedback"} for f in external_feedback]
        )

    scores = []
    for s in sources:
        if s.retro_page:
            feedback.extend(s.retro_page.feedback())
            if score := s.retro_page.feedback_score():
                scores.append(f"{s.retro_page.name}: {score}")

    if level == Level.daily:
        page_content = asyncio.run(aww.retro_gen.page_content(node))
        content.insert(0, page_content)

    return optimize_prompt(
        critique_model_name=critique_model_name,
        llm_model=llm_model,
        current_prompt=current_prompt,
        test_inputs=content,
        feedback=feedback,
        scores=scores,
    )
