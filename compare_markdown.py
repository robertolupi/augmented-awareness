import click
import numpy as np

from aww.analysis import (
    load_embedding_model,
    download_nltk_data,
    extract_sentences_from_markdown,
    get_embeddings,
    find_similar_sentences,
    perform_thematic_clustering,
    visualize_clusters
)
from aww.file_manager import read_file_content


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
    # --- Setup ---
    download_nltk_data()
    embedding_model = load_embedding_model()
    # --- End Setup ---

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
    embeddings1 = get_embeddings(sentences1, embedding_model)
    embeddings2 = get_embeddings(sentences2, embedding_model)

    all_sentences = sentences1 + sentences2
    all_embeddings = np.concatenate([embeddings1, embeddings2])
    sources = ['File 1'] * len(sentences1) + ['File 2'] * len(sentences2)

    click.echo(f"--- Finding similar sentences (threshold > {threshold}) ---")
    similar_pairs = find_similar_sentences(embeddings1, sentences1, embeddings2, sentences2, threshold)
    if not similar_pairs:
        click.echo("No similar sentence pairs found above the threshold.")
    else:
        for pair in similar_pairs:
            click.echo(f"Score: {pair['score']:.4f}")
            click.echo(f"  File 1: {pair['sentence1']}")
            click.echo(f"  File 2: {pair['sentence2']}")

    cluster_labels = None
    if cluster or visualize:
        click.echo("--- Thematic Clustering (DBSCAN) ---")
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
                    click.echo(f"Noise ({len(sentences)} sentences - not part of any theme)")
                    continue
                click.echo(f"Theme {label + 1} ({len(sentences)} sentences):")
                for sent in sentences[:5]:
                    click.echo(f"  - {sent}")

    if visualize:
        if cluster_labels is None:
            click.echo("Cannot visualize without cluster labels. Run with --cluster or more data.")
        else:
            click.echo("--- Generating Visualization ---")
            visualize_clusters(all_embeddings, cluster_labels, sources)
            click.echo(f"Visualization saved to similarity_plot.png")


if __name__ == '__main__':
    main()
