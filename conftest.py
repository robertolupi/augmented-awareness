from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def test_config_file(monkeypatch):
    """Point Settings at the crafted test config instead of the local aww.toml."""
    monkeypatch.setenv(
        "AWW_CONFIG_FILE", str(Path(__file__).parent / "aww.test.toml")
    )
