import datetime
import streamlit as st

from aww.config import Settings
from aww.obsidian import Vault, Level

st.title("Augmented Awareness")

settings = Settings()
vault = Vault.from_settings(settings)

current_page = vault.page(datetime.date.today(), Level.daily)

st.write(current_page.events())
st.write(current_page.content())
