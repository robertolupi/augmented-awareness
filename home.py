import datetime
from pathlib import Path

from aww import obsidian

import streamlit as st

from aww.obsidian import Level

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

col1, col2 = st.columns(2)

with col1:
    if current_page:
        with st.expander("Frontmatter"):
            st.write(current_page.frontmatter())
        st.markdown(current_page.content())
    else:
        st.write("No page found")

with col2:
    if current_retro:
        with st.expander(
            f"Frontmatter ({current_retro.frontmatter().get('model_name')})"
        ):
            st.write(current_retro.frontmatter())
        st.markdown(current_retro.content())
    else:
        st.write("No retrospective page found")
