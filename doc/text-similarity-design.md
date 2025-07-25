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
    *   **Tool:** `nltk` is a lightweight and effective tool for this task.
    *   **Process:** Each cleaned text block will be processed by `nltk.sent_tokenize` to segment it into sentences.

### Stage 2: Sentence Embedding

This stage converts each sentence into a high-dimensional numerical vector (an embedding) that represents its semantic meaning.

1.  **Model:** `sentence-transformers` is the state-of-the-art library for this.
    *   **Recommended Model:** `all-MiniLM-L6-v2` provides an excellent balance of speed and performance.
2.  **Process:** All sentences extracted from both documents will be fed into the chosen model, which will output an embedding for each one.

### Stage 3: Similarity Analysis

This is the core analysis stage, which uses the embeddings to find similarities.

#### Approach A: Direct Sentence Matching

1.  **Technique:** Cosine Similarity.
2.  **Process:** Compute a similarity matrix between sentences from Document A and Document B. Pairs with a score above a configurable threshold are considered matches.

#### Approach B: Thematic Clustering

1.  **Technique:** Density-based clustering.
2.  **Tool:** `scikit-learn`'s `DBSCAN` provides a good balance of performance and simplicity.
3.  **Process:** All sentence embeddings are pooled and clustered to find groups of semantically similar sentences, which represent themes.

### Stage 4: Visualization

1.  **Technique:** `t-SNE` (from `scikit-learn`) for dimensionality reduction.
2.  **Output:** A 2D scatter plot showing sentence clusters, saved as an image file.

## 5. Streamlit User Interface

To make the comparison intuitive and interactive, a Streamlit application will be developed.

### 5.1. UI Components

*   **File Upload:** Two file upload widgets to accept the markdown files.
*   **Side-by-Side View:** The application will display the two markdown files in two columns for easy comparison.
*   **Controls:** The sidebar will contain sliders and inputs to configure analysis parameters (e.g., similarity threshold, DBSCAN `eps` and `min_samples`).
*   **Analysis Button:** A button to trigger the comparison process.
*   **Plot Display:** An area to display the generated t-SNE similarity plot.

### 5.2. Core Feature: Thematic Highlighting

The key feature is to visually highlight sentences that belong to the same thematic cluster across both documents.

1.  **Analysis:** The sentence extraction, embedding, and clustering logic from `compare_markdown.py` will be used as the backend.
2.  **Color Mapping:** A set of distinct background colors will be pre-defined. Each cluster label (theme) will be mapped to a unique color.
3.  **HTML Injection:**
    *   After clustering, the script will have a list of all sentences and their corresponding cluster labels.
    *   The original markdown text for each document will be taken as a single string.
    *   The script will iterate through the list of sentences for that document. For each sentence belonging to a cluster (i.e., label is not -1 for noise), it will be wrapped in an HTML `<span>` tag with the appropriate background color.
    *   **Example:** `This is a sentence.` becomes `<span style="background-color: #FFCC00;">This is a sentence.</span>`
    *   A simple and robust string replacement will be used to inject the HTML into the original markdown text. This approach is chosen for its simplicity in this initial version.
4.  **Rendering:** The final, modified markdown strings (now containing HTML) will be rendered in the Streamlit app using `st.markdown(..., unsafe_allow_html=True)`.

## 6. Key Libraries and Technologies

*   **Web UI:** `streamlit`
*   **Preprocessing:** `markdown-it-py`, `nltk`
*   **Embedding:** `sentence-transformers`
*   **Analysis:** `scikit-learn` (for cosine similarity, DBSCAN, and t-SNE)
*   **Data Handling:** `numpy`
*   **Visualization:** `matplotlib`, `seaborn`

