A loose collection of experiments to build *quantified-self* tools for living a more wholesome life.

# Journal management tool

This program manages a journal of events in Markdown pages, stored in an Obsidian Vault.

Pages are created in Obsidian, they are named after dates (YYYY-MM-DD) and contains a list of events in the
specified section.

Events have the following format:

```markdown

# Events and Journal

Other text can be present in the section, and it will be ignored.

06:05 an event without an end
07:15 - 08:00 an event with an end
text can be interspersed, and it will be ignored.
09:00 - 09:30 events can have hashtags like #tag
```

## Tools

### Journal

This program provides a set of tools, available both on the command line for the user and as an MCP server for
LLMs to use.

```
A simple command line tool to update my journal in Obsidian.

Usage:
  journal [command]

Available Commands:
  amend       Amend the last journal entry
  busy        Show how I spent my time
  completion  Generate the autocompletion script for the specified shell
  help        Help about any command
  index       Index the journal pages
  list        List today events
  mcp         Run as a MCP (Master Control Program) server
  record      Record a new journal entry
  search      Search for pages in the journal
  tasks       List tasks in the given date range
  tui         Start the TUI

Flags:
      --data string      Path to the data directory
  -h, --help             help for journal
      --section string   Section of the journal entry
      --vault string     Path to the Obsidian vault

Use "journal [command] --help" for more information about a command.
```

### Aww

This program provides tools to generate yearly/monthly/weekly/daily retrospectives and to chat with LLMs 
providing access to the user's vault.

```
Usage: aww.py [OPTIONS] COMMAND [ARGS]...

Options:
  --local_model TEXT
  --local_url TEXT
  --gemini_model TEXT
  --openai_model TEXT
  -p, --provider [local|gemini|openai]
  --help                          Show this message and exit.

Commands:
  chat   Interactive chat with LLM access to the user's vault.
  retro  Generate retrospective(s).
```

## Demo

See the [Demonstration vault](demo_vault/demo_vault), which contains a journal based on "[The Sorrows of Young Werther](https://www.gutenberg.org/files/2527/2527-h/2527-h.htm)" by J.W. von Goethe.
