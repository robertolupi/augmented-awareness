# Run this script using the obsidian command:
#
# uv run aww.py obsidian web

import streamlit as st
import os
from aww.observe.obsidian import Vault
from aww.orient.schedule import Schedule


vault_path = os.environ.get("OBSIDIAN_VAULT")
if not vault_path:
    raise ValueError("No OBSIDIAN_VAULT defined in environment")

vault = Vault(vault_path)

date_start = st.date_input("Date start")
date_end = st.date_input("Date end")

journal = vault.journal().subrange(date_start, date_end)
schedule = Schedule(journal)


st.text(f"{len(journal)} pages")

tag_durations = schedule.total_duration_by_tag().to_pandas()

st.dataframe(
    tag_durations,
    column_config={
        "tag": st.column_config.TextColumn("Tag"),
        "histogram": st.column_config.BarChartColumn("Histogram"),
    },
)

for page in journal.values():
    tasks = page.tasks()
    if len(tasks) > 0:
        st.header(page.name)
        for task in tasks:
            st.markdown(str(task))
