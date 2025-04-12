from typing import Tuple

from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider

from .settings import Settings


def get_agent(
    agent_name: str, model_name: str | None = None, settings: Settings | None = None
) -> Tuple[Agent, str]:
    """
    Creates and configures an LLM agent based on the provided settings.

    Args:
        agent_name: Name of the agent configuration to use from settings
        model_name: Optional override for the model specified in agent config
        settings: Optional Settings instance (defaults to global settings)

    Returns:
        Tuple containing:
        - Configured Agent instance ready for use
        - Default user prompt string from agent configuration

    The agent is configured based on the following settings hierarchy:
    1. Looks up agent configuration by agent_name
    2. Uses either specified model_name or agent's default model
    3. Retrieves provider configuration for the selected model
    4. Initializes appropriate provider and model instances

    Currently supports these providers:
    - google-gla: For Gemini models via Google GLA API
    - Default: OpenAI-compatible providers
    """
    settings = settings or Settings()
    agent_config = settings.llm.agent[agent_name]
    model_config = settings.llm.model[model_name or agent_config.model_name]
    provider_config = settings.llm.provider[model_config.provider]

    match model_config.provider:
        case "google-gla":
            provider = GoogleGLAProvider(api_key=provider_config.api_key)
            model = GeminiModel(model_name=model_config.model, provider=provider)
        case _:
            provider = OpenAIProvider(
                api_key=provider_config.api_key, base_url=provider_config.base_url
            )
            model = OpenAIModel(model_name=model_config.model, provider=provider)

    return (
        Agent(
            model=model,
            system_prompt=agent_config.system_prompt,
            model_settings=agent_config.settings,
        ),
        agent_config.user_prompt,
    )
