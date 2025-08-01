import streamlit as st
import datetime
import re
from pathlib import Path
from collections import defaultdict
import pandas
import numpy as np
from sklearn.manifold import TSNE
from sentence_transformers import SentenceTransformer
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from aww import obsidian

# It's good practice to cache the model loading
@st.cache_resource
def load_st_model(model_name):
    return SentenceTransformer(model_name)

def build_palette(size: int, cmap_name: str) -> list[str]:
    cmap = plt.get_cmap(cmap_name)
    return [mcolors.to_hex(cmap(0.2 + 0.8 * i / max(size - 1, 1))) for i in range(size)]

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
            date_end = date_start.replace(year=date_start.year + 1) - datetime.timedelta(days=1)
    date_range = [date_start + datetime.timedelta(days=i) for i in range((date_end - date_start).days + 1)]


st.write("Date Start", date_start, "Date End", date_end, "total", len(date_range), "days")

HASHTAG_RE = re.compile('#[a-zA-Z0-9_/]+')

def extract_tags_and_content(vault, date, level):
    retro_page = vault.retrospective_page(date, level)
    if not retro_page or not retro_page.path.exists():
        return (date, [], "")
    content = retro_page.content()
    tags = HASHTAG_RE.findall(content)
    tags = [tag[1:] for tag in tags]
    return (date, tags, content)

with st.spinner("Loading retrospectives..."):
    dated_tags_content = [extract_tags_and_content(vault, date, obsidian.Level.daily) for date in date_range]
    dated_tags_content = [item for item in dated_tags_content if item[2]] # Filter out empty content
    
    if dated_tags_content:
        # Unzip the data
        dates, tags_list, contents = zip(*dated_tags_content)

        st.header("Tag Analysis")
        # Convert dated_tags to a pandas.DataFrame
        df1 = pandas.DataFrame({'date': dates, 'tags': tags_list})
        st.write(df1)

        # Convert dated_tags to a histogram count of tags, as a pandas.DataFrame
        tag_counts = defaultdict(int)
        for tags in tags_list:
            for tag in tags:
                tag_counts[tag] += 1

        if tag_counts:
            df2 = pandas.DataFrame(list(tag_counts.items()), columns=['tag', 'count'])
            df2 = df2.sort_values(by='count', ascending=False)
            st.write(df2)

            st.text("Pick a tag to show in which days it was mentioned")
            if not df2.empty:
                tag = st.selectbox("Tag", df2['tag'].unique())
                st.write(df1[df1['tags'].apply(lambda x: tag in x)]['date'])
        else:
            st.write("No tags found in the selected date range.")

        st.header("Content-based Clustering")
        default_perplexity = min(30, len(contents) - 1)
        perplexity = st.slider("Perplexity", min_value=3, max_value=min(50, len(contents) - 1), value=default_perplexity)

        if st.button("Cluster Retrospectives"):
            with st.spinner("Embedding and clustering..."):
                model = load_st_model('all-MiniLM-L6-v2')
                embeddings = model.encode(contents, convert_to_tensor=True, normalize_embeddings=True)

                if len(embeddings) <= 3:
                    st.warning(f"Not enough documents to cluster. Need at least 4, but found {len(embeddings)}.")
                    st.stop()

                tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42,
                            init='random', learning_rate=200)
                
                tsne_results = tsne.fit_transform(embeddings.cpu().numpy())

                df_tsne = pandas.DataFrame({
                    'date': dates,
                    'tsne_1': tsne_results[:, 0],
                    'tsne_2': tsne_results[:, 1],
                    'weekday': [d.strftime('%A') for d in dates]
                })

                weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                palette = build_palette(len(weekday_order), 'viridis')
                color_map = {day: color for day, color in zip(weekday_order, palette)}

                fig, ax = plt.subplots(figsize=(12, 10))
                
                for weekday in weekday_order:
                    subset = df_tsne[df_tsne['weekday'] == weekday]
                    if not subset.empty:
                        ax.scatter(subset['tsne_1'], subset['tsne_2'], c=[color_map[weekday]], label=weekday, s=100, alpha=0.7)

                for i, row in df_tsne.iterrows():
                    ax.annotate(row['date'].strftime('%m-%d'), (row['tsne_1'], row['tsne_2']), fontsize=8)

                ax.legend()
                plt.title('t-SNE Clustering of Retrospectives by Content')
                plt.xlabel('t-SNE Dimension 1')
                plt.ylabel('t-SNE Dimension 2')
                st.pyplot(fig)
    else:
        st.write("No retrospectives found in the selected date range.")
