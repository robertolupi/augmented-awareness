from pathlib import Path

from jinja2 import Environment, FileSystemLoader, Template

prompts_path = Path(__file__).parent / "prompts"
prompts_env = Environment(loader=FileSystemLoader(prompts_path))


def get_prompt_template(name: str) -> Template:
    """Get a prompt template, given its name."""
    return prompts_env.get_template(name)
