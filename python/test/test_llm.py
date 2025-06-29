import pathlib

import aww.settings
from aww.llm import get_agent, get_model
from pydantic_ai import Agent
from pydantic_ai.models import Model
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel

test_dir = pathlib.Path(__file__).parent
test_vault_dir = test_dir / "vault"
aww.settings.CONFIG_FILE = test_dir / "config.toml"


def test_get_agent():
    agent, default_user_prompt = get_agent("tips")
    assert isinstance(agent, Agent)
    assert agent.model.model_name == "gemma-3-4b-it"
    assert agent.model.base_url == "http://localhost:1234/v1/"
    assert default_user_prompt == "What can I do differently?"


def test_get_model_local():
    """Test that get_model returns the correct model for local provider."""
    model = get_model("local")
    assert isinstance(model, Model)
    assert isinstance(model, OpenAIModel)
    assert model.model_name == "gemma-3-4b-it"


def test_get_model_gemini():
    """Test that get_model returns the correct model for google-gla provider."""
    model = get_model("gemini")
    assert isinstance(model, Model)
    assert isinstance(model, GeminiModel)
    assert model.model_name == "gemini-2.0-flash"
