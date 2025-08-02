# RAG Options for Retrospective Generation

This document summarizes the discussion on integrating a Retrieval-Augmented Generation (RAG) approach to reduce inference costs while retaining control over the retrospective generation process.

## Core Strategy: Augment, Don't Replace

The primary goal is to reduce the amount of context sent to the language model during retrospective generation. Instead of sending the full content of all source notes, the proposed strategy is to:

1.  **Identify Sources:** Continue using the existing `build_retrospective_tree` logic to determine the precise source notes for a given retrospective (e.g., which daily notes are needed for a weekly summary).
2.  **Retrieve Relevant Snippets:** Use a vector index to perform a similarity search against the content of the source notes. The query would be a high-level concept like "Key events, accomplishments, and challenges for this period."
3.  **Filter for Control:** Critically, filter the search results to **only include snippets from the pre-determined source notes**. This ensures the context remains strictly relevant to the specific retrospective being generated.
4.  **Generate Summary:** Send the smaller, more relevant context (the retrieved snippets) to the LLM for summarization, thus reducing token count and inference cost.

## Vector Index Implementation Options

Three potential libraries were evaluated for implementing the vector index.

### 1. FAISS (from Meta)

*   **Description:** A highly efficient, low-level similarity search library.
*   **Pros:** Maximum performance and control over the indexing and search process.
*   **Cons:** Requires manual management of the index, text chunks, and the mapping between them.

### 2. ChromaDB

*   **Description:** A user-friendly, open-source vector store that runs as a client-server model.
*   **Pros:** Balances ease of use with powerful filtering. Manages the mapping of vectors to documents and metadata automatically. Its API-first design is ideal for multi-language projects.
*   **Cons:** Slightly more overhead than a pure in-memory solution like FAISS, but likely negligible for this use case.

### 3. LanceDB

*   **Description:** A modern, embedded vector store with a focus on performance and ease of use.
*   **Pros:** Excellent performance and a simple API. Manages storage and metadata alongside vectors.
*   **Cons:** As an embedded library, cross-language integration relies on `cgo`, which can add build complexity.

## Language Binding Support

The suitability of each library for this project's multi-language (Python/Go) nature was a key consideration.

| Library  | Python Bindings | Go Bindings      | Key Consideration                                                      |
| :------- | :-------------- | :--------------- | :--------------------------------------------------------------------- |
| **FAISS**    | **Yes (Official)**  | No (Official)    | Go integration would require a complex `cgo` wrapper or a Python service. |
| **ChromaDB** | **Yes (Official)**  | **Yes (Official)** | **Client-server model** makes cross-language support easy via API calls. |
| **LanceDB**  | **Yes (Official)**  | **Yes (Official)** | Go bindings wrap the core Rust library using `cgo`.                    |

## Recommendation

For this project, **ChromaDB** is the most suitable option. Its client-server architecture and official Go client provide the easiest path for both the Python and potential Go components to interact with a shared vector index without the complexities of `cgo`. It offers the best balance of developer experience, performance, and the powerful metadata filtering required to maintain precise control over the retrospective generation logic.
