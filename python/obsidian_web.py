# Run this script using the obsidian command:
#
# uv run aww.py obsidian web

import streamlit as st
import os
from aww.observe.obsidian import Vault


vault_path = os.environ.get("OBSIDIAN_VAULT")
if not vault_path:
    raise ValueError("No OBSIDIAN_VAULT defined in environment")

vault = Vault(vault_path)

st.header(f"Obsidian Vault: {vault_path}")

st.text(f"{len(vault.pages())} pages")

date = st.date_input('Date')

if date:
    page = None
    try:
        page = vault.journal()[date]
    except KeyError:
        st.error("Date not found")
        st.stop()

    st.header(page.name)
    st.markdown(page.content())
