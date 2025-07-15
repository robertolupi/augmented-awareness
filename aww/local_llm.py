from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

lmstudio = OpenAIProvider(base_url='http://localhost:1234/v1')
model = OpenAIModel(model_name='qwen/qwen3-30b-a3b', provider=lmstudio)
