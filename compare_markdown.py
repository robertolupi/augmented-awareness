import streamlit as st

from aww.analysis import (
    download_nltk_data,
    load_embedding_model,
    extract_sentences_from_markdown,
    get_embeddings,
    perform_thematic_clustering
)
from aww.colorizer import colorize_markdown

# --- Setup ---
download_nltk_data()
embedding_model = load_embedding_model()
# --- End Setup ---


# --- UI Layout ---
st.set_page_config(layout="wide")
st.title("Markdown Similarity Comparison")

# Sidebar for controls
st.sidebar.title("Analysis Controls")
eps = st.sidebar.slider("DBSCAN Epsilon (lower for tighter clusters)", 0.1, 1.0, 0.3, 0.05)
min_samples = st.sidebar.slider("DBSCAN Min Samples (higher for denser clusters)", 2, 10, 3, 1)
run_analysis = st.sidebar.button("Run Analysis")

# Initialize session state
if 'analysis_complete' not in st.session_state:
    st.session_state['analysis_complete'] = False
if 'content1' not in st.session_state:
    st.session_state['content1'] = ""
if 'content2' not in st.session_state:
    st.session_state['content2'] = ""

# Main content area
col1, col2 = st.columns(2)

with col1:
    st.header("Document 1")
    file1 = st.file_uploader("Upload the first markdown file", type=['md', 'txt'], key="file1")
    if file1:
        content1 = file1.getvalue().decode("utf-8")
        st.session_state.content1 = content1
    else:
        content1 = ""

    if st.session_state.analysis_complete and st.session_state.content1:
        len_s1 = len(st.session_state.sentences1)
        colorized_content1 = colorize_markdown(
            st.session_state.content1,
            st.session_state.sentences1,
            st.session_state.cluster_labels[:len_s1]
        )
        st.markdown(colorized_content1, unsafe_allow_html=True)
    elif st.session_state.content1:
        st.markdown(st.session_state.content1)


with col2:
    st.header("Document 2")
    file2 = st.file_uploader("Upload the second markdown file", type=['md', 'txt'], key="file2")
    if file2:
        content2 = file2.getvalue().decode("utf-8")
        st.session_state.content2 = content2
    else:
        content2 = ""

    if st.session_state.analysis_complete and st.session_state.content2:
        len_s1 = len(st.session_state.sentences1)
        colorized_content2 = colorize_markdown(
            st.session_state.content2,
            st.session_state.sentences2,
            st.session_state.cluster_labels[len_s1:]
        )
        st.markdown(colorized_content2, unsafe_allow_html=True)
    elif st.session_state.content2:
        st.markdown(st.session_state.content2)


if run_analysis:
    if st.session_state.content1 and st.session_state.content2:
        with st.spinner("Analyzing documents... This may take a moment."):
            sentences1 = extract_sentences_from_markdown(st.session_state.content1)
            sentences2 = extract_sentences_from_markdown(st.session_state.content2)

            all_sentences = sentences1 + sentences2
            all_embeddings = get_embeddings(all_sentences, embedding_model)

            cluster_labels = perform_thematic_clustering(all_embeddings, eps=eps, min_samples=min_samples)

            st.session_state['analysis_complete'] = True
            st.session_state['sentences1'] = sentences1
            st.session_state['sentences2'] = sentences2
            st.session_state['cluster_labels'] = cluster_labels

        st.success("Analysis complete!")
        st.rerun()
    else:
        st.warning("Please upload both files before running the analysis.")