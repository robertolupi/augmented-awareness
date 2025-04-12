from pydantic_ai import Agent
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider
from pydantic_ai.providers.openai import OpenAIProvider

from .settings import Settings


def get_agent(
    agent_name: str, model_name: str | None = None, settings: Settings | None = None
) -> (Agent, str):
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
