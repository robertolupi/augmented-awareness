# Agents Code-Assist Guide

This document provides guidance for using agents to assist with development in this project. This is a multi-language project, which will include Go and Python.

## Obsidian Vault structure

Markdown files hold notes inside the Obsidian vault.

Augmented Awareness expect a vault organized in the following directories (journal, and retrospectives are mandatory; others are optional):

- `0-inbox`: new notes, that I am still writing and working on.
- `1-projects`: project notes (GTD projects).
- `2-areas`: areas of responsibility (health, family, house, work, etc.).
- `3-resources`: miscellaneous notes that are useful to consult for reference, or as data storage for information (e.g. pages for my collection of photography gear, etc.).
- `4-archive:` archived notes that I do not need to actively consult.
- `journal`: Journal files
  - `journal/yyyy` (e.g. `journal/2025`): a directory for each year.
  - `journal/yyyy/Yyyyy.md` (e.g. `journal/2025/Y2025.md`): yearly note, containing long-term goals and plans (e.g. GTD "Horizons of Focus" style).
  - `journal/yyyy/mm` (e.g. `journal/2025/01`): a directory for each year and month.
    - `journal/yyyy/mm/yyyy-mm-dd.md` (e.g. `journal/2025/01/2025-01-02.md` for January 2nd, 2025): daily notes.
    - `journal/yyyy/months/yyyy-mm.md` (e.g. `journal/2025/months/2025-01.md` for January 2025): monthly notes.
    - `journal/yyyy/weeks/yyyy-Www.md` (e.g. `journal/2025/weeks/2025-W01.md` for the first week of 2025): weekly notes.
- `retrospectives`: Retrospective notes, which are summaries and reflections on journal entries. The file names are prefixed with `r`.
  - `retrospectives/yyyy/ryyyy.md` (e.g. `retrospectives/2025/r2025.md`): yearly retrospective.
  - `retrospectives/yyyy/mm/ryyyy-mm-dd.md` (e.g. `retrospectives/2025/01/r2025-01-02.md`): daily retrospective.
  - `retrospectives/yyyy/months/ryyyy-mm.md` (e.g. `retrospectives/2025/months/r2025-01.md`): monthly retrospective.
  - `retrospectives/yyyy/weeks/ryyyy-Www.md` (e.g. `retrospectives/2025/weeks/r2025-W01.md`): weekly retrospective.

## Project Structure

The project is organized by language.

### Go

The Go portion of the application follows the standard Go project layout:

-   `cmd/`: Contains the main application entry points. Each subdirectory is a separate command.
-   `internal/`: Contains the core application logic. This code is not intended to be imported by other projects.
    -   `internal/application`: Core application services.
    -   `internal/config`: Configuration management.
    -   `internal/datetime`: Time and date utilities.
    -   `internal/obsidian`: Code for interacting with Obsidian vaults.
    -   `internal/search`: Search and indexing functionality.
    -   `internal/tui`: Terminal user interface components.
-   `pkg/`: (Not yet present) Would contain library code that's okay to be used by external applications.
-   `go.mod`, `go.sum`: Go module definitions and dependencies.

### Python

The Python code provides tools for generating retrospectives from journal entries.

-   `aww.py`: The main CLI entry point, built with `click`. It allows users to generate retrospectives for different time periods (daily, weekly, etc.) using various language models.
-   `aww/`: The main Python package.
    -   `config.py`: Manages application settings using Pydantic.
    -   `obsidian.py`: Contains classes (`Vault`, `Page`) for interacting with the structure of an Obsidian vault.
    -   `retro.py`: Implements the core logic for generating retrospectives. It builds a dependency tree of notes and uses an AI agent to summarize them.
    -   `retro/`: This directory contains the Markdown-based system prompts that guide the AI model for generating daily, weekly, monthly, and yearly retrospectives.
-   `test_*.py`: Unit tests for the Python modules.

#### Dependency Management

Use `uv add` for python dependencies and to run python programs, such as `aww.py` itself or `streamlit`.

```bash
uv add streamlit
```


## Testing

Ignore `demo_vault` it is not relevant for development: it doesn't contain code or test data, but a demo based on a book (its length will overwhelm agents).

### Go Testing

To run all Go tests in this project, use the following command from the project root:

```bash
go test ./...
```

### Python Testing

To run all Python tests in this project, use `pytest` from the project root:

```bash
PYTHONPATH=. uv run pytest
```

To run a specific test file:

```bash
PYTHONPATH=. uv run pytest path/to/test_file.py
```

### General Best Practices

-   **Write Tests for New Code:** All new features, bug fixes, or refactors should be accompanied by corresponding tests, regardless of the language.
-   **Keep Tests Focused:** Tests should be small and focused on a single unit of behavior.
-   **Use Language-Idiomatic Testing:** Use standard testing patterns for the language you are working in (e.g., table-driven tests in Go).
-   **Check for Coverage:** Use language-specific tools (like `go test -cover`) to check test coverage and identify areas that need more testing.

By following these guidelines, we can ensure the project remains reliable and maintainable.
