# Agents Code-Assist Guide

This document provides guidance for using agents to assist with development in this project. This is a multi-language project, which includes Go and Python.

## Obsidian Vault structure

Markdown files hold notes inside the Obsidian vault.

Augmented Awareness expects a vault organized in the following directories (journal, and retrospectives are mandatory; others are optional):

- `0-inbox`: new notes, that I am still writing and working on.
- `1-projects`: project notes (GTD projects).
- `2-areas`: areas of responsibility (health, family, house, work, etc.).
- `3-resources`: miscellaneous notes that are useful to consult for reference, or as data storage for information (e.g. pages for my collection of photography gear, etc.).
- `4-archive`: archived notes that I do not need to actively consult.
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

The Go module is named `journal` and builds a single CLI binary:

-   `journal.go`: The main entry point (`package main`, calls `cmd.Execute()`).
-   `cmd/`: The Cobra commands of the `journal` CLI (`record`, `stop`, `busy`, `list`, `amend`, `index`, `search`, `tasks`, `tasks-cleanup`, `pomodoro`, `tui`, `mcp`).
-   `internal/`: Contains the core application logic. This code is not intended to be imported by other projects.
    -   `internal/application`: Core application services (busy, search, tasks).
    -   `internal/config`: Configuration management (viper).
    -   `internal/datetime`: Time and date utilities.
    -   `internal/mcptools`: MCP server exposing vault tools (read journal/pages/retros/tasks, remember, search, busy, config, datetime).
    -   `internal/obsidian`: Code for interacting with Obsidian vaults (vault/page/task/event parsing).
    -   `internal/search`: Search and indexing functionality (bleve).
    -   `internal/stats`: Busy-time metrics and histograms.
    -   `internal/tui`: Terminal user interface components (bubbletea).
-   `pkg/`: (Not yet present) Would contain library code that's okay to be used by external applications.
-   `go.mod`, `go.sum`: Go module definitions and dependencies.

### Python

The Python code provides tools for generating retrospectives from journal entries, plus chat, ask, MOTD, and search workflows.

-   `aww_run.py`: The main Python CLI entry point, built with `click` and backed by `aww.cli:main`. It allows users to generate retrospectives for different time periods (daily, weekly, etc.) using various language models.
-   `aww/`: The main Python package.
    -   `config.py`: Manages application settings using Pydantic (env vars with `AWW_` prefix, `.env`, and `aww.toml`).
    -   `obsidian.py`: Contains classes (`Vault`, `Page`) for interacting with the structure of an Obsidian vault.
    -   `retro.py`: Period expansion (day, Monday–Sunday ISO week, month, year) and the retrospective dependency graph.
    -   `retro_gen.py`: Recursive retrospective generation using a pydantic-ai agent, with cache policies and output metadata.
    -   `chat.py`, `tools.py`, `session_manager.py`, `rag.py`: Tool-calling chat, SQLite session storage, and LanceDB/sentence-transformers search.
    -   `cli/`: The Click subcommands (`retro`, `ask`, `chat`, `compare`, `motd`, `index`, `search`, `tags`, `taskscleanup`, `rewrite_prompt`, `show_config`).
    -   `prompts/`: The Markdown-based system prompts (Jinja) that guide the AI model for daily, weekly, monthly, and yearly retrospectives, plus `ask_*`, `chat`, `motd`, and `compare` prompts.
-   `home.py`, `pages/`: Streamlit UI (chat, side-by-side retrospective comparison, tag analysis).
-   `tests/`: Unit tests for the Python modules; some tests also live alongside the code as `aww/test_*.py`.

#### Dependency Management

Use `uv add` for python dependencies and `uv run` to execute Python programs, such as `aww_run.py`, the installed `aww` console script, or `streamlit`.

```bash
uv add streamlit
```

### Obsidian Plugin (TypeScript)

The `obsidian-plugin/` directory contains the native Obsidian desktop plugin (`aww-retro`):

- `src/main.ts`: Main plugin entry point, registering views, settings tab, ribbon icons, and commands.
- `src/settings.ts`: Settings definitions and configuration UI.
- `src/adapters/`: Interfaces with the Obsidian `aiProviders` plugin (`Model.ts`).
- `src/core/`: Core application logic:
  - `core/plan.ts`: Retrospective dependency resolution DAG.
  - `core/generate.ts`: Retrospective generation pipeline.
  - `core/tools/`: Read-only vault tools (`search_vault`, `read_pages`, `read_journal`, `read_retro`, `read_tasks`, `list_dates`, `extract_metric`, `datetime`, `calculator`).
  - `core/chat/`: Chat agent, multi-turn tool calling, session management, and system prompts.
- `src/ui/`: UI components (`ChatView.ts`, `GenerateModal.ts`, `ProgressNotice.ts`).
- `styles.css`: Obsidian native CSS styling.
- `tests/`: Vitest test suites.

Build commands:
- Build: `cd obsidian-plugin && npm run build`
- Tests: `cd obsidian-plugin && npm test`


## Testing

Do not read `demo_vault` wholesale: it contains no code or unit-test data, only a demo vault based on a book, and its length will overwhelm agents. It is, however, the read-only seed for the disposable vaults used in Obsidian plugin development — see `doc/obsidian-plugin-design.md` (work on copies of it, never against the main vault).

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

### Obsidian Plugin Testing & UI Verification

#### Unit Testing
To run all plugin unit tests:

```bash
cd obsidian-plugin && npm test
```

#### Hot-Reloading in Obsidian
When modifying plugin code or styles, build and reload in the active vault:

```bash
cd obsidian-plugin && npm run build
cp obsidian-plugin/main.js obsidian-plugin/styles.css /Users/rlupi/data/notes/.obsidian/plugins/aww-retro/
obsidian plugin:reload id=aww-retro vault=notes
```

#### UI Screenshots (IMPORTANT)
**ALWAYS use `obsidian dev:screenshot` instead of macOS `screencapture`**:

```bash
obsidian dev:screenshot path=/path/to/screenshot.png vault=notes
```

Benefits:
- **No macOS Screen Recording permissions needed**: Uses Obsidian's internal Electron/Chromium capture directly.
- **Strict window cropping**: Captures only the Obsidian window, cleanly omitting the user's desktop, other open apps, or OS menubar.
- **Fast and resilient**: Works reliably regardless of display sleep or space switching.

### General Best Practices

-   **Write Tests for New Code:** All new features, bug fixes, or refactors should be accompanied by corresponding tests, regardless of the language.
-   **Keep Tests Focused:** Tests should be small and focused on a single unit of behavior.
-   **Use Language-Idiomatic Testing:** Use standard testing patterns for the language you are working in (e.g., table-driven tests in Go).
-   **Check for Coverage:** Use language-specific tools (like `go test -cover`) to check test coverage and identify areas that need more testing.

By following these guidelines, we can ensure the project remains reliable and maintainable.
