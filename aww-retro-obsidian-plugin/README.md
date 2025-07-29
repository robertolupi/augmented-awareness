# Aww Retrospectives Obsidian Plugin

This plugin helps you manage and generate daily, weekly, monthly, and yearly retrospectives by summarizing your journal notes.

## Features

-   **Flexible Timeframes:** Supports daily, weekly, monthly, and yearly retrospectives.

## How it Works

The plugin scans your Obsidian vault for journal notes that follow a specific naming convention. 

### Naming Convention

To use this plugin, your journal and retrospective notes must follow these naming patterns:

#### Journal Notes

-   **Daily:** `YYYY-MM-DD.md` (e.g., `2025-01-02.md`)
-   **Weekly:** `gggg-Www.md` (e.g., `2025-W01.md`)
-   **Monthly:** `YYYY-MM.md` (e.g., `2025-01.md`)
-   **Yearly:** `YYYY.md` (e.g., `2025.md`)

#### Retrospective Notes

Retrospective notes are automatically named by prepending an 'r' to the journal note's name:

-   **Daily:** `rYYYY-MM-DD.md` (e.g., `r2025-01-02.md`)
-   **Weekly:** `rgggg-Www.md` (e.g., `r2025-W01.md`)
-   **Monthly:** `rYYYY-MM.md` (e.g., `r2025-01.md`)
-   **Yearly:** `rYYYY.md` (e.g., `r2025.md`)
