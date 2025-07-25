# Markdown Text Similarity Analysis Design

## 1. Objective

To define a robust process for comparing two markdown documents to identify and analyze semantic similarities. The analysis will operate on two levels:
1.  **Direct Sentence-to-Sentence Similarity:** Finding pairs of sentences that convey the same meaning.
2.  **Thematic Similarity:** Identifying common topics or themes discussed across both documents.

## 2. Refined Plan

The process is broken down into four main stages: Preprocessing, Embedding, Analysis, and Visualization.

### Stage 1: Preprocessing and Sentence Extraction

The goal of this stage is to reliably extract clean sentences from the markdown text while preserving their document of origin.

1.  **Markdown Cleaning:** Raw markdown text is not ideal for sentence splitting due to its syntax (e.g., headers, lists, links, code blocks). The first step is to convert the markdown into clean, structured plain text.
    *   **Method:** Use a library like `markdown-it-py` to parse the markdown. A custom renderer will be used to handle different element types:
        *   Headers, paragraphs, and list items will be treated as standard text.
        *   Links will be converted to just their text description.
        *   Code blocks will be ignored, as they do not typically contain natural language sentences for comparison.
2.  **Sentence Segmentation (Splitting):** Once the text is cleaned, it can be split into individual sentences.
    *   **Tool:** `spaCy` is the ideal tool for this task due to its accuracy.
    *   **Process:** Each cleaned text block will be processed by a `spaCy` pipeline (e.g., `en_core_web_sm`), which will segment it into sentences. Each extracted sentence will be stored along with a reference to its source document (Document A or Document B).

### Stage 2: Sentence Embedding

This stage converts each sentence into a high-dimensional numerical vector (an embedding) that represents its semantic meaning.

1.  **Model:** `sentence-transformers` is the state-of-the-art library for this.
    *   **Recommended Model:** `all-MiniLM-L6-v2` provides an excellent balance of speed and performance, making it a great starting point.
    *   **Alternative (Higher Accuracy):** For higher accuracy at the cost of speed, `all-mpnet-base-v2` can be used.
2.  **Process:** All sentences extracted from both documents will be fed into the chosen model, which will output an embedding for each one.

### Stage 3: Similarity Analysis

This is the core analysis stage, which uses the embeddings to find similarities. We will use two complementary approaches.

#### Approach A: Direct Sentence Matching

This approach finds specific, similar sentence pairs across the two documents.

1.  **Technique:** Cosine Similarity.
2.  **Process:**
    *   A similarity matrix will be computed where each cell `(i, j)` contains the cosine similarity score between sentence `i` from Document A and sentence `j` from Document B.
    *   A threshold (e.g., > 0.75) is applied to this matrix to identify pairs of sentences with high semantic similarity.
3.  **Output:** A list of sentence pairs, one from each document, that are semantically equivalent, along with their similarity score.

#### Approach B: Thematic Clustering

This approach identifies broader topics or themes that are common to both documents.

1.  **Technique:** Density-based clustering.
2.  **Tool:** `HDBSCAN` is recommended over `DBSCAN` because it does not require specifying the `eps` parameter, can find a variable number of clusters, and is robust to noise (i.e., it can classify sentences that don't belong to any theme as outliers).
3.  **Process:**
    *   All sentence embeddings from both documents are pooled into a single dataset.
    *   `HDBSCAN` is run on this dataset to group semantically similar sentences into clusters.
    *   Each cluster is then analyzed based on the origin of its member sentences:
        *   **Shared Theme:** A cluster containing a significant mix of sentences from both Document A and Document B represents a common theme.
        *   **Unique Theme:** A cluster composed almost entirely of sentences from one document represents a theme unique to that document.
4.  **Output:** A list of themes (clusters). For each theme, we can provide representative sentences (e.g., the sentences closest to the cluster's centroid) and label it as "Shared," "Document A Only," or "Document B Only."

### Stage 4: Visualization (Optional but Recommended)

To make the results easier to interpret, the high-dimensional embeddings can be projected into 2D space.

1.  **Technique:** `UMAP` (Uniform Manifold Approximation and Projection) is an excellent technique for dimensionality reduction that preserves the data's global structure.
2.  **Process:**
    *   Run `UMAP` on all sentence embeddings to get a 2D coordinate for each sentence.
    *   Create a scatter plot of these points.
    *   The points can be colored based on their source document (Document A vs. B) or their assigned theme (cluster ID from HDBSCAN).
3.  **Output:** A 2D plot that visually shows the relationships between sentences and the identified thematic clusters.

## 3. Key Libraries and Technologies

*   **Preprocessing:** `markdown-it-py`, `spacy`
*   **Embedding:** `sentence-transformers` (using PyTorch)
*   **Analysis:** `scikit-learn` (for cosine similarity), `hdbscan`
*   **Data Handling:** `numpy`
*   **Visualization:** `matplotlib`, `seaborn`, `umap-learn`
