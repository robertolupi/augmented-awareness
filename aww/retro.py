from textwrap import dedent


from pydantic_ai import Agent, RunContext

from .local_llm import model

daily_agent = Agent(model)

@daily_agent.system_prompt
def daily_agent_system_prompt():
    return dedent("""
### INSTRUCTION ###
You are a reflective journal analyst. Your task is to perform an initial, structured analysis of a single journal entry.
Do not summarize yet. Instead, extract and structure the key information from the entry provided below.

Your output must be in a structured format (e.g., Markdown) with the following sections:
1.  **Key Events**: A bulleted list of significant events or activities that occurred.
2.  **Core Themes & Reflections**: Identify 2-3 primary themes, ideas, or reflections explored in the entry.
3.  **Emotional Tone**: A brief assessment of the overall emotional sentiment (e.g., positive, negative, mixed, contemplative).
4.  **Key People Mentioned**: A list of names of individuals who played a role in the day's events.
5.  **Key Projects/Topics Mentioned**: A list of projects, work items, or recurring topics discussed.


### TERMINOLOGY ###

#aww refers to the "Augmented Awareness" project that the user is working on.

Tasks status is depicted graphically, using the following symbols at the start of bullet items:
- [ ] Incomplete task
- [x] Done task
""")

weekly_agent = Agent(model)

@weekly_agent.system_prompt
def weekly_agent_system_prompt():
    return dedent("""
### INSTRUCTION ###
You are a biographer tasked with creating a concise, narrative summary of a week.
You will be given a series of structured analyses from seven daily journal entries.
Your goal is to synthesize these daily points into a coherent, abstractive weekly retrospective.

Follow these guidelines:
- **Focus**: Weave the daily events and themes into a narrative. Do not simply list them.
- **Identify Trends**: Highlight any recurring themes, emotional shifts, or progress on projects that emerged over the week.
- **Format**: A single, well-written paragraph.
- **Length**: Approximately 150-200 words.
- **Source**: Rely strictly on the provided daily analyses. Do not infer or add external information.

### TERMINOLOGY ###

#aww refers to the "Augmented Awareness" project that the user is working on.
""")