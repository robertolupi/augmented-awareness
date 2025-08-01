import streamlit as st
import datetime
import re
from pathlib import Path
from collections import defaultdict
import pandas

from aww import obsidian

with st.sidebar:
    vault_path = st.text_input("Vault path", value="~/data/notes")
    journal_dir = st.text_input("Journal dir", value="journal")
    retrospectives_dir = st.text_input("Retrospectives", value="retrospectives")
    if vault_path and journal_dir and retrospectives_dir:
        vault_path = Path(vault_path).expanduser()
        if vault_path.exists():
            vault = obsidian.Vault(vault_path, journal_dir, retrospectives_dir)
            st.badge("Vault OK", color="green")
    
    date_start = st.date_input("Date", datetime.date.today())
    scope = st.selectbox("Scope", ["Weekly", "Monthly", "Yearly"])
    match scope:
        case "Weekly":
            date_start = date_start - datetime.timedelta(days=date_start.weekday())
            date_end = date_start + datetime.timedelta(days=6)
        case "Monthly":
            date_start = date_start.replace(day=1)
            date_end = (date_start + datetime.timedelta(days=31)).replace(day=1) - datetime.timedelta(days=1)
        case "Yearly":
            date_start = date_start.replace(month=1, day=1)
            date_end = date_start.replace(year=1) - datetime.timedelta(days=1)
    date_range = [date_start + datetime.timedelta(days=i) for i in range((date_end - date_start).days + 1)]
    
    
st.write("Date Start", date_start, "Date End", date_end, "total", len(date_range), "days")

HASHTAG_RE = re.compile('#[a-zA-Z0-9_/]+')

def extract_tags(vault, date, level):
    retro_page = vault.retrospective_page(date, level)
    if not retro_page:
        return (date, [])
    content = retro_page.content()
    tags = HASHTAG_RE.findall(content)
    tags = [tag[1:] for tag in tags]
    return (date, tags)

with st.spinner():
    dated_tags = [extract_tags(vault, date, obsidian.Level.daily) for date in date_range]
    # Convert dated_tags to a pandas.DataFrame
    df1 = pandas.DataFrame(dated_tags, columns=['date', 'tags'])
    st.write(df1)
    
    # Convert dated_tags to a histogram count of tags, as a pandas.DataFrame
    tag_counts = defaultdict(int)
    for date, tags in dated_tags:
        for tag in tags:
            tag_counts[tag] += 1
            
    df2 = pandas.DataFrame(list(tag_counts.items()), columns=['tag', 'count'])
    df2 = df2.sort_values(by='count', ascending=False)
    st.write(df2)

st.text("Pick a tag to show in which days it was mentioned")
tag = st.selectbox("Tag", df2['tag'].unique())
st.write(df1[df1['tags'].apply(lambda x: tag in x)]['date'])