import datetime
from pathlib import Path

from aww import obsidian

import streamlit as st

from aww.obsidian import Level, Page

st.set_page_config(layout="wide")
st.header("Home")

with st.sidebar:
    vault_path = st.text_input("Vault Path", "~/data/notes")
    date = st.date_input("Date", datetime.date.today())
    level = st.selectbox(
        "Level",
        options=list(Level),
    )

vault = obsidian.Vault(Path(vault_path).expanduser(), "journal", "retrospectives")


current_page = vault.page(date, level)
current_retro = vault.retrospective_page(date, level)

alternative_retros = [
    Page(p, level)
    for p in sorted(current_retro.path.parent.glob(current_retro.path.stem + "*.md"))
]

col1, col2 = st.columns(2)

with col1:
    if current_page:
        with st.expander("Frontmatter"):
            st.write(current_page.frontmatter())
        events = current_page.events()
        if len(events):
            st.write(events)
        st.markdown(current_page.content())
    else:
        st.write("No page found")

with col2:
    if alternative_retros:

        def page_name(p: Page) -> str:
            return f"{p.name} ({p.frontmatter().get('model_name')})"

        alternatives = [page_name(a) for a in alternative_retros]
        tabs = st.tabs(alternatives)
        for tab, retro in zip(tabs, alternative_retros):
            with tab:
                with st.expander("Frontmatter"):
                    st.write(retro.frontmatter())
                st.markdown(retro.content())
    else:
        st.write("No retrospective pages found")
