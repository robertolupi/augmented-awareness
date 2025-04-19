# Development Guidelines for Augmented Awareness (aww)

This document provides guidelines and instructions for developing and maintaining the Augmented Awareness project.

## Build/Configuration Instructions

### Environment Setup

1. The project requires Python 3.13 or higher.
2. Use a virtual environment for development:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

### Dependencies

Dependencies are managed through `pyproject.toml`. Install them using a compatible package manager:

```bash
# Using pip
pip install -e .

# Using uv (recommended)
uv pip install -e .
```

### Configuration

The application uses a TOML configuration file located at:
- `~/.config/aww/config.toml` (Linux/macOS)
- `%APPDATA%\aww\config\config.toml` (Windows)

Example configuration structure:

```toml
[obsidian]
vault = "~/Documents/Obsidian Vault"  # Path to Obsidian vault

[llm.provider.local]
base_url = "http://localhost:1234/v1/"

[llm.provider.google-gla]
api_key = "YOUR_API_KEY"

[llm.provider.openai]
api_key = "YOUR_API_KEY"

[llm.model.local]
provider = "local"
model = "gemma-3-4b-it"

[llm.model.gemini]
provider = "google-gla"
model = "gemini-2.0-flash"

[llm.agent.tips]
model_name = "local"
system_prompt = """Your system prompt here"""
user_prompt = "Default user prompt"
```

## Testing Information

### Running Tests

The project uses pytest for testing. Run tests with:

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest test/test_llm.py

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=aww
```

### Adding New Tests

1. Create test files in the `test/` directory with the naming pattern `test_*.py`
2. Use the pytest framework for writing tests
3. For tests that require configuration, use the test configuration file:

```python
import pathlib
import aww.settings

# Set up test environment
test_dir = pathlib.Path(__file__).parent
aww.settings.CONFIG_FILE = test_dir / "config.toml"
```

### Test Example

Here's a simple test example for the `get_model` function:

```python
import pathlib
import pytest
from pydantic_ai.models import Model
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.models.openai import OpenAIModel

import aww.settings
from aww.llm import get_model

test_dir = pathlib.Path(__file__).parent
aww.settings.CONFIG_FILE = test_dir / "config.toml"

def test_get_model_local():
    """Test that get_model returns the correct model for local provider."""
    model = get_model("local")
    assert isinstance(model, Model)
    assert isinstance(model, OpenAIModel)
    assert model.model_name == "gemma-3-4b-it"

def test_get_model_gemini():
    """Test that get_model returns the correct model for google-gla provider."""
    model = get_model("gemini")
    assert isinstance(model, Model)
    assert isinstance(model, GeminiModel)
    assert model.model_name == "gemini-2.0-flash"
```

## Code Style and Development Guidelines

### Code Organization

The code is organized according to the Observe-Orient-Decide-Act (OODA) loop:

1. **Observe:** Code in `aww/observe/` - Gather raw data from sensors or external sources
2. **Orient:** Code in `aww/orient/` - Transform or interpret data into meaningful insights
3. **Decide:** Decision-making logic
4. **Act:** Code in `aww/commands/` - Carry out decisions through actuators

### Data Store

The data store acts as a whiteboard for multiple kinds of agents:
- **Observers** publish data
- **Orienters** read raw data, aggregate or summarize it, and write back insights
- **Deciders** read insights, generate decisions, and publish them
- **Actuators** read decisions and execute actions

### Code Style

The project uses Ruff for linting and formatting. Run Ruff with:

```bash
# Check code style
ruff check .

# Format code
ruff format .
```

### Documentation

- Use docstrings for all public functions, classes, and methods
- Follow Google-style docstrings format
- Include type hints for function parameters and return values