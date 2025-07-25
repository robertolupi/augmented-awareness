import click
from markdown_it import MarkdownIt
from sentence_transformers import SentenceTransformer, util
import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
import seaborn as sns
import nltk

# --- NLTK setup ---
# Download the 'punkt' tokenizer models if not already present
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    print("Downloading NLTK models...")
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
# --- End NLTK setup ---


# Load the sentence-transformer model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def read_file_content(filepath):
    """Reads the content of a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def extract_sentences_from_markdown(markdown_content):
    """
    Cleans markdown and extracts a list of sentences using NLTK.
    """
    md = MarkdownIt()
    text = md.render(markdown_content)
    sentences = nltk.sent_tokenize(text)
    return [sent.strip() for sent in sentences if sent.strip()]

def get_embeddings(sentences):
    """
    Generates embeddings for a list of sentences.
    """
    return embedding_model.encode(sentences, show_progress_bar=True)

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

def perform_thematic_clustering(embeddings, eps=0.5, min_samples=5):
    """
    Performs thematic clustering using DBSCAN and returns the cluster labels.
    """
    if len(embeddings) < min_samples:
        return None
    clusterer = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    return clusterer.fit_predict(embeddings)

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
    click.echo(f"Visualization saved to {output_filename}")

@click.command()
@click.argument('file1', type=click.Path(exists=True))
@click.argument('file2', type=click.Path(exists=True))
@click.option('--threshold', default=0.75, help='Similarity threshold for sentence matching.')
@click.option('--cluster', is_flag=True, help='Enable thematic clustering analysis.')
@click.option('--eps', default=0.3, help='DBSCAN epsilon parameter.')
@click.option('--min-samples', default=3, help='DBSCAN min_samples parameter.')
@click.option('--visualize', is_flag=True, help='Generate a t-SNE visualization of the sentence clusters.')
def main(file1, file2, threshold, cluster, eps, min_samples, visualize):
    """
    Compares two markdown files for semantic similarity.
    """
    click.echo(f"Comparing {file1} and {file2}")
    
    content1 = read_file_content(file1)
    content2 = read_file_content(file2)

    click.echo("Files read successfully. Extracting sentences...")
    sentences1 = extract_sentences_from_markdown(content1)
    sentences2 = extract_sentences_from_markdown(content2)
    click.echo(f"Extracted {len(sentences1)} sentences from {file1}.")
    click.echo(f"Extracted {len(sentences2)} sentences from {file2}.")

    if not sentences1 or not sentences2:
        click.echo("One or both files have no sentences to compare. Exiting.")
        return

    click.echo("Generating embeddings...")
    embeddings1 = get_embeddings(sentences1)
    embeddings2 = get_embeddings(sentences2)
    
    all_sentences = sentences1 + sentences2
    all_embeddings = np.concatenate([embeddings1, embeddings2])
    sources = ['File 1'] * len(sentences1) + ['File 2'] * len(sentences2)

    click.echo(f"\n--- Finding similar sentences (threshold > {threshold}) ---")
    similar_pairs = find_similar_sentences(embeddings1, sentences1, embeddings2, sentences2, threshold)
    if not similar_pairs:
        click.echo("No similar sentence pairs found above the threshold.")
    else:
        for pair in similar_pairs:
            click.echo(f"\nScore: {pair['score']:.4f}")
            click.echo(f"  File 1: {pair['sentence1']}")
            click.echo(f"  File 2: {pair['sentence2']}")

    cluster_labels = None
    if cluster or visualize:
        click.echo("\n--- Thematic Clustering (DBSCAN) ---")
        cluster_labels = perform_thematic_clustering(all_embeddings, eps=eps, min_samples=min_samples)
        if cluster_labels is None:
            click.echo("Not enough sentences to perform clustering.")
        elif cluster:
            clustered_sentences = {}
            for i, label in enumerate(cluster_labels):
                if label not in clustered_sentences:
                    clustered_sentences[label] = []
                clustered_sentences[label].append(all_sentences[i])
            
            for label, sentences in clustered_sentences.items():
                if label == -1:
                    click.echo(f"\nNoise ({len(sentences)} sentences - not part of any theme)")
                    continue
                click.echo(f"\nTheme {label + 1} ({len(sentences)} sentences):")
                for sent in sentences[:5]: # Show up to 5 example sentences
                    click.echo(f"  - {sent}")

    if visualize:
        if cluster_labels is None:
            click.echo("\nCannot visualize without cluster labels. Run with --cluster or more data.")
        else:
            click.echo("\n--- Generating Visualization ---")
            visualize_clusters(all_embeddings, cluster_labels, sources)

if __name__ == '__main__':
    main()