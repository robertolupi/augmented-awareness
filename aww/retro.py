from textwrap import dedent


from pydantic_ai import Agent, RunContext

from .local_llm import model

agent = Agent(model)

@agent.system_prompt
def retrospective_system_prompt():
    return dedent("""
    You will receive the user journal as input, and your job is write a retrospective summarizing its
    content in 5 bullet points.
    
    Then answer these questions:
    - Is the user improving or stagnant?
    - What could the user do differently, that they haven't thought about yet? Provide 3 action items.
""")