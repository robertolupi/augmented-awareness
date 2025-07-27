import asyncio
import io

import nltk
import streamlit as st
from nltk.tokenize import sent_tokenize
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from sentence_transformers import SentenceTransformer, util

import yaml

from aww.colorizer import build_palette_map
from aww.obsidian import FRONTMATTER_RE
from aww.analysis import download_nltk_data, extract_sentences_from_markdown


class ComparisonResult(BaseModel):
    in_both: list[str]
    only_in_first: list[str]
    only_in_second: list[str]


def get_file_content(f: io.BytesIO, prop: str|None='model_name') -> [str, str]:
    s = f.getvalue().decode('utf-8')
    if m := FRONTMATTER_RE.match(s):
        front_matter = yaml.safe_load(m.group(1))
        p = front_matter.get(prop)
        return str(p), FRONTMATTER_RE.sub('', s)
    return '', s


def colorize_concepts(md: str, palette: dict[str, str], normalize: bool = True,
                      threshold : float = 0.6) -> str:
    concepts = list(palette.keys())
    sentences = extract_sentences_from_markdown(md)
    st_model = SentenceTransformer('all-MiniLM-L6-v2')
    emb_sentences = st_model.encode(sentences, convert_to_tensor=True, normalize_embeddings=normalize)
    emb_concepts = st_model.encode(concepts, convert_to_tensor=True, normalize_embeddings=normalize)
    
    for i, s in enumerate(sentences):
        sims = util.cos_sim(emb_sentences[i], emb_concepts)[0]
        # Compute the highest score above threshold
        highest_score = 0
        closest_concept = None
        for j, score in enumerate(sims):
            if score > highest_score and score > threshold:
                highest_score = score
                closest_concept = concepts[j]
        if closest_concept:
            md = md.replace(s, f'<span style="color: {palette[closest_concept]}">{s}</span>')
    return md


st.set_page_config(layout="wide")
st.title("Markdown Similarity Comparison")

with st.spinner("Downloading dependencies..."):
    download_nltk_data()

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

model1, doc1 = get_file_content(file1) if file1 else (None, None)
model2, doc2 = get_file_content(file2) if file2 else (None, None)

if doc1 and doc2 and do_compare:
    with st.spinner("Comparison in progress"):
        comparison_agent = Agent(
            model=model,
            output_type=ComparisonResult,
            instructions="Compare the following documents and identify concepts and entities that are present in both, only in the first, only in the second.")
        agent_result = asyncio.run(comparison_agent.run(f"First document:\n{doc1}\n---\nSecond document:\n{doc2}\n"))
        # st.write(agent_result.output)

        result: ComparisonResult = agent_result.output

        col1, common, col2 = st.columns(3)
        palette = build_palette_map([result.in_both, result.only_in_first, result.only_in_second],
                                    ["Greens", "Reds", "Blues"])
        with col1:
            for s in result.only_in_first:
                st.markdown(f"<span style='color: {palette[s]}'>{s}</span>", unsafe_allow_html=True)
        with common:
            for s in result.in_both:
                st.markdown(f"<span style='color: {palette[s]}'>{s}</span>", unsafe_allow_html=True)
        with col2:
            for s in result.only_in_second:
                st.markdown(f"<span style='color: {palette[s]}'>{s}</span>", unsafe_allow_html=True)

        doc1 = colorize_concepts(doc1, palette)
        doc2 = colorize_concepts(doc2, palette)
else:
    result = None
    palette = None

col1, col2 = st.columns(2)

with col1:
    st.header(model1)
    st.markdown(doc1, unsafe_allow_html=True)

with col2:
    st.header(model2)
    st.markdown(doc2, unsafe_allow_html=True)
