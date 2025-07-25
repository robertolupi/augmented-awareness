import nltk
import numpy as np
import seaborn as sns
from markdown_it import MarkdownIt
from matplotlib import pyplot as plt
from sentence_transformers import SentenceTransformer, util
from sklearn.cluster import DBSCAN
from sklearn.manifold import TSNE


# --- Model Loading ---
def load_embedding_model():
    return SentenceTransformer('all-MiniLM-L6-v2')


# --- NLTK setup ---
def download_nltk_data():
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        nltk.download('punkt', quiet=True)


def extract_sentences_from_markdown(markdown_content):
    """Tokenizes markdown content into sentences, preserving markdown syntax."""
    sentences = nltk.sent_tokenize(markdown_content)
    return [sent.strip() for sent in sentences if sent.strip()]


def get_embeddings(sentences, embedding_model):
    """Generates embeddings for a list of sentences."""
    return embedding_model.encode(sentences, show_progress_bar=True)


def perform_thematic_clustering(embeddings, eps=0.5, min_samples=5):
    """Performs thematic clustering using DBSCAN and returns the cluster labels."""
    if len(embeddings) < min_samples:
        return None
    clusterer = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    return clusterer.fit_predict(embeddings)


def find_similar_sentences(embeddings1, sentences1, embeddings2, sentences2, threshold):
    """
    Finds and prints pairs of similar sentences above a given threshold.
    """
    cosine_scores = util.cos_sim(embeddings1, embeddings2)
    similar_pairs = []
    for i in range(len(sentences1)):
        for j in range(len(sentences2)):
            if cosine_scores[i][j] > threshold:
                similar_pairs.append({
                    "score": cosine_scores[i][j],
                    "sentence1": sentences1[i],
                    "sentence2": sentences2[j]
                })
    return sorted(similar_pairs, key=lambda x: x['score'], reverse=True)


def visualize_clusters(embeddings, labels, sources, output_filename="similarity_plot.png"):
    """
    Visualizes sentence embeddings and their clusters using t-SNE.
    """
    tsne = TSNE(n_components=2, perplexity=15, random_state=42, metric='cosine')
    reduced_embeddings = tsne.fit_transform(embeddings)

    df = {
        'x': reduced_embeddings[:, 0],
        'y': reduced_embeddings[:, 1],
        'label': labels,
        'source': sources
    }

    plt.figure(figsize=(12, 10))
    palette = sns.color_palette("deep", np.unique(labels).max() + 1)
    sns.scatterplot(data=df, x='x', y='y', hue='label', style='source', palette=palette, s=50)

    plt.title("Sentence Embeddings Visualized with t-SNE")
    plt.xlabel("t-SNE Dimension 1")
    plt.ylabel("t-SNE Dimension 2")
    plt.legend(title='Cluster')
    plt.savefig(output_filename)
