# RAG and Full-Text Search Design Document

This document outlines the design for implementing a Retrieval-Augmented Generation (RAG) system and full-text search for the `journal` application.

## 1. Overview

The goal is to enhance the search capabilities of the `journal` tool and introduce a RAG system to allow for more natural and powerful interaction with the journal entries. This will be achieved by:

1.  **Implementing a full-text search index:** This will allow for fast and accurate searching of the entire content of the journal pages.
2.  **Creating a vector store:** This will store vector embeddings of the journal pages, enabling semantic search.
3.  **Developing a RAG pipeline:** This will use the search results to retrieve relevant context and generate answers to user queries using a Large Language Model (LLM).

## 2. System Architecture

The system will consist of the following components:

-   **Indexer:** A new component responsible for creating and maintaining the full-text search index and the vector store.
-   **Searcher:** A component that queries the index and vector store to retrieve relevant pages.
-   **RAG Pipeline:** A component that orchestrates the process of retrieving context, generating prompts, and interacting with the LLM.
-   **CLI Command:** A new `search` command that uses the `Searcher` to provide enhanced search results.
-   **MCP Tool:** A new MCP tool that uses the RAG pipeline to answer user queries.

## 3. Detailed Design

### 3.1. Indexer

The `Indexer` will be responsible for creating and maintaining the full-text search index and the vector store.

-   **Full-Text Search Index:** We will use the `bleve` library to create a full-text search index. The index will be stored in a file within the user's data directory. The index will be updated automatically whenever a journal page is created or modified.
-   **Vector Store:** We will use the `faiss` library to create a vector store. The vector store will be stored in a file alongside the full-text search index. We will use a pre-trained sentence-transformer model (e.g., `all-MiniLM-L6-v2`) to generate embeddings for each journal page.

A new `index` command will be added to the CLI to allow users to manually trigger the indexing process.

### 3.2. Searcher (Hybrid Search)

To achieve the best possible retrieval results, the `Searcher` will implement a **hybrid search** strategy. This approach combines the strengths of two distinct search methodologies: keyword-based full-text search and semantic vector search.

#### 3.2.1. Rationale for Hybrid Search

-   **Keyword Search (via Bleve):** This method excels at precision and finding documents with specific, literal terms. It's the ideal tool for locating documents based on exact keywords, names, acronyms, or other unique identifiers (e.g., searching for `"Project-X"` or a specific error code). Its limitation is that it has no understanding of language semantics; it would fail to find a document about "feeling unproductive" if the user searches for "lazy day."

-   **Semantic Search (via Faiss):** This method excels at understanding user intent and finding conceptually related documents, even if they don't share keywords. It's perfect for natural language queries (e.g., searching for *"how can I better organize my notes?"* might find a document about *"using headings and bullet points to structure thoughts"*). Its limitation is that it can be too "fuzzy" and may fail to prioritize documents containing a critical but specific keyword if the overall semantic meaning isn't a perfect match.

By combining both, we create a system that is both **precise** and **conceptually aware**. This ensures the RAG pipeline receives the most relevant possible context, dramatically improving the quality of its generated answers.

#### 3.2.2. Search and Re-ranking Process

The `Searcher` will provide a unified interface that orchestrates the hybrid search and re-ranking process.

1.  **Parallel Querying:** The user's query is sent to both the `bleve` index (for keyword matches) and the `faiss` vector store (for semantic matches) simultaneously.
    -   The `bleve` search will return a list of documents with a relevance score (e.g., TF-IDF or BM25 score).
    -   The `faiss` search will return a list of documents with a similarity score (e.g., cosine similarity).

2.  **Score Normalization:** The scores from `bleve` and `faiss` are not directly comparable. Before they can be combined, they must be normalized to a common scale (e.g., 0.0 to 1.0).

3.  **Reciprocal Rank Fusion (RRF) for Re-ranking:** The two lists of results will be combined using a **Reciprocal Rank Fusion (RRF)** algorithm. RRF is a simple yet highly effective "late fusion" technique that is robust and doesn't require complex parameter tuning.

    The process is as follows:
    a. For each document, we get its rank in the `bleve` results list (`rank_bleve`) and its rank in the `faiss` results list (`rank_faiss`). If a document is not in a list, its rank is considered infinite.
    b. The RRF score for each document is calculated using the formula:
       ```
       RRF_score = (1 / (k + rank_bleve)) + (1 / (k + rank_faiss))
       ```
       The constant `k` (typically set to a small value like 60) is used to diminish the impact of documents with very low ranks.
    c. All unique documents from both lists are compiled and sorted in descending order based on their final `RRF_score`.

4.  **Final Results:** The newly sorted list represents the final, re-ranked result set, which is then passed to the RAG pipeline or displayed to the user. This list contains the most relevant documents, benefiting from both keyword precision and semantic understanding.


### 3.3. RAG Pipeline

The RAG pipeline will be implemented as a new MCP tool.

-   It will take a user query as input.
-   It will use the `Searcher` to retrieve the top-k most relevant journal pages.
-   It will construct a prompt for the LLM, including the user query and the content of the retrieved pages.
-   It will send the prompt to the LLM and return the generated answer to the user.

### 3.4. CLI Command

The existing `search` command will be updated to use the new `Searcher`.

-   It will take a user query as input.
-   It will display a ranked list of search results, including the page title and a snippet of the content.

### 3.5. MCP Tool

A new MCP tool, `rag-search`, will be added.

-   It will take a user query as input.
-   It will use the RAG pipeline to generate an answer.
-   It will return the answer to the user.

## 4. Implementation Plan

1.  **Add `bleve` and `faiss` dependencies:** Add the necessary `bleve` and `faiss` Go modules to the `go.mod` file.
2.  **Implement the `Indexer`:** Create a new `internal/search/indexer.go` file and implement the indexing logic.
3.  **Implement the `Searcher`:** Create a new `internal/search/searcher.go` file and implement the search logic.
4.  **Update the `search` command:** Modify `cmd/search.go` to use the new `Searcher`.
5.  **Implement the `rag-search` MCP tool:** Modify `internal/mcptools/search.go` to add the new `rag-search` tool.
6.  **Add tests:** Add unit tests for the `Indexer` and `Searcher` components.

## 5. Future Work

-   **Incremental Indexing:** Implement incremental indexing to improve performance for large journals.
-   **More Sophisticated Re-ranking:** Explore more advanced re-ranking algorithms to improve the quality of the search results.
-   **Support for Different Embedding Models:** Allow users to choose different embedding models.

## 6. Evaluation and Fine-Tuning

To ensure the search system is effective, a robust evaluation and tuning process is required. This involves creating a "golden dataset" and using it to measure the performance of our retrieval system.

### 6.1. Creating a Golden Dataset

A golden dataset is a curated set of queries and their expected results, which serves as the ground truth for our evaluation.

1.  **Query Selection:** We will manually create a list of 20-30 representative queries. These queries should cover a wide range of topics and formats, including:
    *   **Keyword-heavy queries:** "meeting with Project-X"
    *   **Natural language questions:** "what were my main goals last week?"
    *   **Vague or fuzzy queries:** "thoughts on productivity"
    *   **Queries with no expected results.**

2.  **Manual Annotation:** For each query, we will manually search through the journal and identify the set of all relevant documents. This creates a `(query, [relevant_document_ids])` pair.

### 6.2. Evaluation Metrics

We will use standard information retrieval metrics to evaluate the performance of our hybrid search system against the golden dataset. The primary metrics will be:

-   **Mean Reciprocal Rank (MRR):** Measures the average rank of the *first* relevant document. It's useful for evaluating how quickly a user finds what they are looking for.
-   **Normalized Discounted Cumulative Gain (nDCG@k):** Evaluates the quality of the ranking for the top `k` results, considering both the relevance and the position of the retrieved documents. This is crucial for RAG, as the quality of the top few documents directly impacts the LLM's generated answer.
-   **Precision@k and Recall@k:** Measure the fraction of retrieved documents that are relevant (Precision) and the fraction of all relevant documents that are retrieved (Recall) within the top `k` results.

### 6.3. Fine-Tuning `bleve` (Keyword Search)

The performance of `bleve` can be tuned by customizing the analysis pipeline.

-   **Analyzers:** We will experiment with different text analyzers. The standard analyzer is a good starting point, but we can create custom analyzers to better handle specific content in the journals, such as:
    *   **Stop Words:** Customizing the list of stop words (e.g., "a", "the", "in") to be more domain-specific.
    *   **Stemmers and Lemmatizers:** Experimenting with different stemming algorithms (e.g., Porter, Snowball) to see which provides the best results for the journal's language.
    *   **Tokenizers:** Using different tokenizers if the journal contains structured data (e.g., code snippets, URLs) that needs special handling.
-   **Scoring:** `bleve` defaults to TF-IDF. We can switch to the more modern **BM25** scoring algorithm, which often provides better results, and tune its `k1` and `b` parameters using our golden dataset.

### 6.4. Fine-Tuning `faiss` (Semantic Search)

Tuning the semantic search component involves both the embedding model and the `faiss` index itself.

-   **Embedding Model:** The initial choice is `all-MiniLM-L6-v2`. If evaluation shows poor performance on domain-specific terms, we could consider fine-tuning a sentence-transformer model on the journal data itself, though this is a complex process reserved for future work.
-   **Chunking Strategy:** The quality of embeddings depends heavily on the "chunk" of text being embedded. We will experiment with different chunking strategies:
    *   **Whole Document:** Simple, but can dilute the meaning of long documents.
    *   **Fixed-size Chunks:** Splitting documents into fixed-size chunks (e.g., 256 tokens) with some overlap.
    *   **Sentence-based Chunking:** Splitting documents by sentences.
    We will evaluate which chunking strategy yields the best performance on our golden dataset.
-   **Faiss Index Type:** `faiss` offers many index types that trade speed for accuracy.
    *   **IndexFlatL2:** The default, providing exact, brute-force search. It's perfectly acceptable for thousands of documents.
    *   **IVF (Inverted File) Indexes:** If the number of documents grows into the tens of thousands, we can switch to an `IVFFlat` index to speed up search by partitioning the vector space. We would need to tune the number of partitions (`nlist`).

### 6.5. Tuning the Hybrid Re-ranking

The RRF re-ranking algorithm has one main parameter to tune:
-   **The `k` constant:** We will experiment with different values for `k` in the RRF formula (`1 / (k + rank)`). A lower `k` gives more weight to higher-ranked items, while a higher `k` smooths the scores. We will use our golden dataset to find the optimal `k` value that maximizes our evaluation metrics (like nDCG@k).

