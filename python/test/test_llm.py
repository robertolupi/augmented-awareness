import pathlib

from pydantic_ai import Agent

import aww.settings
from aww.llm import get_agent

test_dir = pathlib.Path(__file__).parent
test_vault_dir = test_dir / "vault"
aww.settings.CONFIG_FILE = test_dir / "config.toml"


def test_get_agent():
    agent, default_user_prompt = get_agent("tips")
    assert isinstance(agent, Agent)
    assert agent.model.model_name == "gemma-3-4b-it"
    assert agent.model.base_url == "http://localhost:1234/v1/"
    assert default_user_prompt == "What can I do differently?"
