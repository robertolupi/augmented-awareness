# Augmented Awareness

Augmented Awareness is a sophisticated tool designed to enhance self-reflection and insight by summarizing and analyzing journal entries maintained within an Obsidian vault. It helps users distill key thoughts, patterns, and progress over various timeframes by automatically generating daily, weekly, monthly, and yearly retrospectives.

## Core Concepts

The system is built around the idea of maintaining a structured journal and using AI-powered tools to create meaningful summaries, fostering a deeper level of self-awareness.

### Obsidian Vault Structure

To function correctly, Augmented Awareness expects a specific folder structure within your Obsidian vault:

-   **`journal/`**: The heart of your reflections. It is organized chronologically:
    -   `journal/yyyy/mm/yyyy-mm-dd.md`: Daily notes.
    -   `journal/yyyy/weeks/yyyy-Www.md`: Weekly notes.
    -   `journal/yyyy/months/yyyy-mm.md`: Monthly notes.
    -   `journal/yyyy/Yyyyy.md`: Yearly notes.
-   **`retrospectives/`**: Contains the AI-generated summaries. The file names mirror the journal structure but are prefixed with an `r`:
    -   `ryyyy-mm-dd.md`, `ryyyy-Www.md`, etc.
-   **Other Directories**: `0-inbox`, `1-projects`, `2-areas`, `3-resources`, and `4-archive` for general note-taking and organization, following GTD principles.

## Project Components

Augmented Awareness is a multi-language project composed of several key components:

### 1. Go Tools

The Go portion of the project provides a set of command-line utilities for interacting with the Obsidian vault. These tools handle file operations, indexing, and other core functionalities.

-   **`cmd/`**: Main application entry points.
-   **`internal/`**: Core application logic for configuration, interacting with Obsidian, search, and more.

### 2. Python Tools

The Python component is responsible for the AI-powered generation of retrospectives.

-   **`aww.py`**: A command-line interface (CLI) for triggering the retrospective generation process.
-   **`aww/`**: The core Python package containing logic for:
    -   Managing configuration (`config.py`).
    -   Interacting with the Obsidian vault structure (`obsidian.py`).
    -   Generating summaries with AI models (`retro.py`).

### 3. Obsidian Plugin

An Obsidian plugin is available to help with navigation within the vault, making it easier to move between journal entries and their corresponding retrospectives.

### 4. Side-by-Side (SBS) Viewer

The `sbs` directory contains an interactive, full-stack SvelteKit application designed for debugging. It allows you to view journal pages and their corresponding generated retrospectives side-by-side in a web interface, which is useful for verifying the output and behavior of the generation tools.

## Getting Started

The easiest way to begin using Augmented Awareness is to start with a pre-configured Obsidian vault. The `demo_vault` included in this project provides a ready-to-use setup with all the necessary plugins and folder structures.

1.  **Copy the Demo Vault**: Make a copy of the `/demo_vault/demo_vault` directory and place it wherever you keep your Obsidian vaults. You can rename it to whatever you like.

2.  **Clean the Vault**: Inside your new vault copy, delete the `journal` and `retrospectives` directories. These contain demo content and are best started fresh.

3.  **Open in Obsidian**: Open your new vault in Obsidian. The vault is already configured with the required community plugins, including:
    *   Periodic Notes
    *   Templater
    *   Dataview
    *   Obsidian Tasks
    *   Calendar
    *   Aww-Retro Obsidian Plugin

4.  **Start Journaling**: You can now start creating your own journal entries. The "Periodic Notes" plugin is configured to create daily, weekly, and monthly notes in the correct locations.
