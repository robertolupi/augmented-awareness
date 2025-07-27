import streamlit as st
import asyncio
from aww.obsidian import FRONTMATTER_RE

from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.openai import OpenAIProvider

st.set_page_config(layout="wide")
st.title("Markdown Similarity Comparison")

with st.sidebar:
    st.title("Analysis Controls")
    provider = st.selectbox("Provider", ["gemini", "openai", "local"], index=0)
    match provider:
        case "gemini":
            model_name = st.selectbox("Model", ["gemini-2.5-flash", "gemini-2.5-pro"])
            if model_name:
                model = GoogleModel(model_name=model_name)
        case "openai":
            model_name = st.selectbox("Model", ["gpt-4.1", "o4-mini"])
            if model_name:
                model = OpenAIModel(model_name=model_name)
        case "local":
            base_url = st.text_input("Base URL", "http://localhost:1234/v1")
            model_name = st.text_input("Model")
            if base_url and model_name:
                model = OpenAIModel(model_name=model_name, provider=OpenAIProvider(base_url=base_url))
    
    file1 = st.file_uploader("First file", type=["md", "txt"])
    file2 = st.file_uploader("Second file", type=["md", "txt"])
    if file1 and file2:
        do_compare = st.button("Compare")
    else:
        do_compare = None

def strip_frontmatter(s:str) -> str:
    return FRONTMATTER_RE.sub('', s)

doc1 = strip_frontmatter(file1.getvalue().decode('utf-8')) if file1 else None
doc2 = strip_frontmatter(file2.getvalue().decode('utf-8')) if file2 else None

class ComparisonResult(BaseModel):
    in_both: list[str]
    only_in_first : list[str]
    only_in_second: list[str]

if do_compare:
    with st.spinner("Comparison in progress"):
        comparison_agent = Agent(
            model=model,
            output_type=ComparisonResult,
            instructions="Compare the following documents and identify concepts and entities that are present in both, only in the first, only in the second.")
        agent_result = asyncio.run(comparison_agent.run(f"First document:\n{doc1}\n---\nSecond document:\n{doc2}\n"))
        st.write(agent_result.output)
else:
    agent_result = None

col1, col2 = st.columns(2)

with col1:
    st.markdown(doc1)
    
with col2:
    st.markdown(doc2)