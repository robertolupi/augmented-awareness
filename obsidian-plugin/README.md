# AWW Retrospectives (`aww-retro`)

Native Obsidian desktop plugin for Augmented Awareness, generating AI-powered retrospectives across daily, weekly, monthly, and yearly horizons.

## Overview

AWW Retrospectives reads your Obsidian vault journal notes and aggregates them into multi-horizon retrospectives. It operates entirely inside Obsidian, interacting with local or cloud language models (such as LM Studio, Ollama, OpenRouter, or OpenAI) through the [AI Providers](https://github.com/pfrankov/obsidian-ai-providers) plugin.

## Key Features

- **Multi-Level Horizons**: Generates Daily (`YYYY-MM-DD`), Weekly (`YYYY-Www`), Monthly (`YYYY-MM`), and Yearly (`YYYY`) retrospectives.
- **DAG Dependency Planner**: Higher-level retrospectives automatically resolve and aggregate lower-level dependencies (e.g. Monthly aggregates weeks and daily journal notes).
- **Smart Modification Invalidation (`mtime`)**: Reuses up-to-date retrospectives without redundant model calls unless source journal notes have changed since the retrospective was created.
- **Safe Archiving**: Existing retrospectives are never silently overwritten; they are backed up progressively (`rYYYY-MM-DD.1.md`, `.2.md`, etc.), preserving history.
- **Options Modal with Live Plan Preview**: The "Generate retrospective with options..." command provides a date picker, level dropdown, force-regeneration toggle, and a live preview of expected model calls and dependency resolution before execution.
- **Visual Progress & In-Flight Cancellation**: Native Obsidian progress bar displays real-time step status with an immediate Cancel button backed by `AbortController`.
- **Configurable Input Filters**: Customize ignored journal headings (case-insensitive) and frontmatter metric extractors (stress, sleep, mood, meditation, etc.) matching Python Augmented Awareness rules.

## Requirements

- **Obsidian**: 1.12.7+ (Desktop only).
- **AI Providers Plugin**: [obsidian-ai-providers](https://github.com/pfrankov/obsidian-ai-providers) installed and enabled in your vault, configured with at least one provider (e.g. LM Studio, OpenRouter, OpenAI, or Anthropic).

## Installation

### From Source

1. Clone or navigate to the repository:
   ```bash
   cd obsidian-plugin
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Build the production bundle:
   ```bash
   npm run build
   ```
4. Copy or symlink the plugin folder into your vault:
   ```bash
   mkdir -p /path/to/your/vault/.obsidian/plugins/aww-retro
   cp manifest.json main.js /path/to/your/vault/.obsidian/plugins/aww-retro/
   ```
5. In Obsidian:
   - Open **Settings** -> **Community plugins**.
   - Reload installed plugins and enable **AWW Retrospectives**.
   - Open **Settings** -> **AWW Retrospectives** to choose your AI Providers model.

## Available Commands

| Command ID | Name | Description |
|---|---|---|
| `aww-retro:generate-retrospective-active-note` | Generate retrospective for active note | Infers date & level from the active note, always forcing root regeneration. |
| `aww-retro:generate-retrospective-options` | Generate retrospective with options... | Opens interactive dialog with date picker, level selector, force toggle, and real-time plan preview. |
| `aww-retro:generate-daily-retrospective` | Generate daily retrospective | Generates daily retrospective for active note's date (or today), reusing up-to-date targets. |
| `aww-retro:generate-weekly-retrospective` | Generate weekly retrospective | Generates weekly retrospective (`YYYY-Www`), resolving daily dependencies. |
| `aww-retro:generate-monthly-retrospective` | Generate monthly retrospective | Generates monthly retrospective (`YYYY-MM`), resolving weekly and daily dependencies. |
| `aww-retro:generate-yearly-retrospective` | Generate yearly retrospective | Generates yearly retrospective (`YYYY`), resolving monthly, weekly, and daily dependencies. |

## Development & Testing

- Run test suite:
  ```bash
  npm test
  ```
- Build plugin:
  ```bash
  npm run build
  ```
- Dev vault helpers in `scripts/`:
  - `make-dev-vault.sh`: Creates a disposable test vault from `demo_vault`.
  - `reset-dev-vault.sh`: Resets test vault to clean state.
  - `wait-for-file.sh`: CLI utility for automation to wait for note generation.
