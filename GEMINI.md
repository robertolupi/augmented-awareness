# Gemini Code-Assist Guide

This document provides guidance for using Gemini to assist with development in this project. This is a multi-language project, which will include Go and Python.

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

## Testing

### Go Testing

To run all Go tests in this project, use the following command from the project root:

```bash
go test ./internal/...
```

#### Why not `go test ./...`?

The standard `go test ./...` command will fail because the Go portion of this project contains multiple `main` packages (in the `cmd/` directory and the root). The `go test` command is designed to test library packages, not executable `main` packages. The command `go test ./internal/...` specifically targets the testable library code within the `internal/` directory.

### General Best Practices

-   **Write Tests for New Code:** All new features, bug fixes, or refactors should be accompanied by corresponding tests, regardless of the language.
-   **Keep Tests Focused:** Tests should be small and focused on a single unit of behavior.
-   **Use Language-Idiomatic Testing:** Use standard testing patterns for the language you are working in (e.g., table-driven tests in Go).
-   **Check for Coverage:** Use language-specific tools (like `go test -cover`) to check test coverage and identify areas that need more testing.

By following these guidelines, we can ensure the project remains reliable and maintainable.