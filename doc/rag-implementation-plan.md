# RAG Implementation Plan

This document provides a step-by-step plan for implementing the Retrieval-Augmented Generation (RAG) system as outlined in the `rag-search-design.md`. This plan assumes that the FTS implementation is either complete or being worked on in parallel.

## Phase 1: Vector Store and Hybrid Search

### Step 1: Add Dependencies
- **Action:** Add the `faiss` and a suitable sentence-transformer Go library to the `go.mod` file.
- **Commands:**
    - `go get github.com/some-faiss-go-binding` (Note: A specific Go binding for Faiss needs to be chosen, e.g., from a C-binding).
    - `go get github.com/some-sentence-transformer-library` (Note: A library for using models like `all-MiniLM-L6-v2` needs to be selected).

### Step 2: Extend the Indexer for Vector Embeddings
- **File:** `internal/search/indexer.go`.
- **Actions:**
    1.  Modify the `Indexer` struct to also hold a `faiss.Index` instance and the sentence-transformer model.
    2.  Update `NewIndexer` to also load or create the `faiss` index file.
    3.  Implement a **chunking strategy**. Create a helper function `chunkPage(page obsidian.Page)` that splits a page's content into smaller, meaningful chunks (e.g., paragraphs or fixed-size overlapping chunks).
    4.  In the `IndexPage` method, after indexing the page in `bleve`, iterate through the chunks of the page:
        a. Generate a vector embedding for each chunk using the sentence-transformer model.
        b. Add the resulting vector to the `faiss` index, keeping a mapping between the vector ID and the page/chunk it belongs to.
    5.  Update the `index` command to manage both the `bleve` and `faiss` indexes.

### Step 3: Implement Hybrid Search
- **File:** `internal/search/searcher.go`.
- **Actions:**
    1.  Modify the `Searcher` struct to also hold the `faiss.Index` and the embedding model.
    2.  Create a `SearchSemantic(query string)` method:
        a. Generate an embedding for the user's query.
        b. Use the query embedding to search the `faiss` index.
        c. Return a ranked list of page/chunk IDs and their similarity scores.
    3.  Create a `SearchHybrid(query string)` method that implements the full hybrid search and re-ranking logic:
        a. Call `Search()` (for `bleve`) and `SearchSemantic()` in parallel.
        b. Normalize the scores from both search results to a common scale (e.g., 0-1).
        c. Implement the **Reciprocal Rank Fusion (RRF)** algorithm to combine the two result lists.
        d. Return a single, re-ranked list of the most relevant pages/chunks.

## Phase 2: RAG Pipeline and MCP Integration

### Step 4: Implement the RAG Pipeline
- **File:** Create `internal/rag/pipeline.go`.
- **Actions:**
    1.  Define a `Pipeline` struct that holds a `search.Searcher` instance.
    2.  Implement a `GenerateAnswer(query string)` method:
        a. Call the `Searcher.SearchHybrid(query)` method to get the top-k most relevant document chunks.
        b. Retrieve the full text of these chunks.
        c. Construct a detailed prompt for the LLM. The prompt should include the original user query and the retrieved context, clearly separated.
        d. Send the prompt to the LLM via the existing MCP infrastructure.
        e. Return the LLM's generated answer.

### Step 5: Create the `rag-search` MCP Tool
- **File:** Modify `internal/mcptools/search.go`.
- **Actions:**
    1.  Create a new MCP tool named `rag-search`.
    2.  This tool will take a user's natural language query as input.
    3.  It will instantiate and use the `rag.Pipeline` to generate an answer.
    4.  The tool will return the generated answer as its result.

## Phase 3: Evaluation and Fine-Tuning

### Step 6: Create the Golden Dataset
- **Action:** Manually create a golden dataset as described in the design document. This will be a JSON or YAML file containing a list of queries and the expected best-matching document IDs.
- **Location:** `testdata/golden_dataset.json`.

### Step 7: Implement Evaluation Scripts
- **Directory:** Create a new directory `scripts/evaluation`.
- **Actions:**
    1.  Create a Go program or script that:
        a. Loads the golden dataset.
        b. Runs each query through the `SearchHybrid` method.
        c. Compares the results against the golden dataset's expected outcomes.
        d. Calculates and prints the evaluation metrics (MRR, nDCG@k, Precision@k, Recall@k).
    2.  This script will be crucial for tuning the system.

### Step 8: Fine-Tune the System
- **Actions:**
    1.  Use the evaluation script to experiment with and find the optimal parameters for:
        -   The RRF `k` constant in `searcher.go`.
        -   The chunking strategy in `indexer.go`.
        -   `bleve` and `faiss` index parameters.
    2.  Document the best-performing parameters.

## Phase 4: Testing

### Step 9: Add Unit and Integration Tests
- **Files:** Create `internal/rag/pipeline_test.go` and add tests to `internal/search/searcher_test.go`.
- **Actions:**
    1.  Write unit tests for the hybrid search to ensure RRF is working correctly.
    2.  Write integration tests for the RAG pipeline, mocking the LLM call, to ensure that context is being retrieved and passed to the prompt correctly.
    3.  Use a small, static test dataset of pages for these tests.
