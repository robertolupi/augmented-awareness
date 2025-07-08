# Gemini Code Assistant Report

This document provides a summary of the `journal` repository, along with tips and best practices for improving the codebase.

## Repository Summary

The `journal` program is a command-line tool for managing a journal of events in Markdown pages, stored in an Obsidian Vault. It allows users to record, list, amend, and search for events in their journal. The tool is written in Go and uses the `cobra` library for command-line parsing, `bubbletea` for the terminal user interface (TUI), and `testify` for testing.

A key feature of this program is the "Master Control Program" (MCP) server, which exposes journal entries and tasks to Large Language Models (LLMs). This allows for powerful integrations with other tools and services.

The codebase is well-structured, with a clear separation of concerns between the command-line interface (in the `cmd` directory) and the core logic (in the `internal` directory). The `internal` directory is further divided into packages for interacting with Obsidian, managing statistics, and handling the TUI.

## Configuration

The `journal` program can be configured via a configuration file, environment variables, or command-line flags. The configuration file is named `.journal.yaml` and should be placed in the user's home directory.

The following configuration options are available:

| Name | YAML Key | Environment Variable | Command-line Flag | Default Value |
|---|---|---|---|---|
| Vault Path | `vault.path` | `JOURNAL_VAULT_PATH` | `--vault` | `~/data/notes` |
| Journal Section | `journal.section` | `JOURNAL_JOURNAL_SECTION` | `--section` | `Journal and events` |

Configuration is loaded in the following order of precedence:

1. Command-line flags
2. Environment variables
3. Configuration file
4. Default values

## Testing

When adding new code, it is important to also add tests to ensure that the code is working correctly and to prevent regressions. The `testify` library is used for testing in this project. When adding a new feature, please add a corresponding test file (e.g., `feature_test.go`) in the same package.

