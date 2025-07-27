import streamlit as st
import asyncio
from aww.obsidian import FRONTMATTER_RE

from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.openai import OpenAIProvider
import io 
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer, util


class ComparisonResult(BaseModel):
    in_both: list[str]
    only_in_first : list[str]
    only_in_second: list[str]
    
def get_file_content(f: io.BytesIO) -> str:
    s = f.getvalue().decode('utf-8')
    return FRONTMATTER_RE.sub('', s)

def build_palette(size: int, cmap_name: str) -> list[str]:
    cmap = plt.get_cmap(cmap_name)
    return [mcolors.to_hex(cmap(0.2 + 0.8*i / max(size-1, 1))) for i in range(size)]

def build_palette_map(result: ComparisonResult, cmaps: tuple[str,str,str]) -> dict[str, str]:
    common_cols = build_palette(len(result.in_both), cmaps[0])
    only_in_first_cols = build_palette(len(result.only_in_first), cmaps[1])
    only_in_second_cols = build_palette(len(result.only_in_second), cmaps[2])
    palette = {
        **{c: col for c, col in zip(result.in_both, common_cols)},
        **{c: col for c, col in zip(result.only_in_first, only_in_first_cols)},
        **{c: col for c, col in zip(result.only_in_second, only_in_second_cols)}
    }
    return palette


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

doc1 = get_file_content(file1) if file1 else None
doc2 = get_file_content(file2) if file2 else None


if do_compare:
    with st.spinner("Comparison in progress"):
        comparison_agent = Agent(
            model=model,
            output_type=ComparisonResult,
            instructions="Compare the following documents and identify concepts and entities that are present in both, only in the first, only in the second.")
        agent_result = asyncio.run(comparison_agent.run(f"First document:\n{doc1}\n---\nSecond document:\n{doc2}\n"))
        # st.write(agent_result.output)
        
        col1, common, col2 = st.columns(3)
        palette = build_palette_map(agent_result.output, ["Greens", "Reds", "Blues"])
        with col1:
            for s in agent_result.output.only_in_first:
                st.markdown(f"<span style='color: {palette[s]}'>{s}</span>", unsafe_allow_html=True)
        with common:
            for s in agent_result.output.in_both:
                st.markdown(f"<span style='color: {palette[s]}'>{s}</span>", unsafe_allow_html=True)
        with col2:
            for s in agent_result.output.only_in_second:
                st.markdown(f"<span style='color: {palette[s]}'>{s}</span>", unsafe_allow_html=True)
else:
    agent_result = None

col1, col2 = st.columns(2)

with col1:
    st.markdown(doc1)
    
with col2:
    st.markdown(doc2)