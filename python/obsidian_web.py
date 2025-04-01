# Run this script using the obsidian command:
#
# uv run obsidian.py /path/to/your/vault web

import streamlit as st
import os
from aww.observe.obsidian import Vault


vault_path = os.environ.get("OBSIDIAN_VAULT")
if not vault_path:
    raise ValueError("No OBSIDIAN_VAULT defined in environment")

vault = Vault(vault_path)

st.header(f"Obsidian Vault: {vault_path}")

st.text(f"{len(vault.pages())} pages")

date, page = list(vault.journal().items())[-1]
st.text(date)
st.markdown(page.content())