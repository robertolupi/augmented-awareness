"""This module acts as a global singletons container.

There is no point in having separate classes just for dependency injection.
"""

from sqlalchemy import Engine
from sqlmodel import create_engine

import aww.datastore.models  # noqa
from aww.observe.obsidian import Journal, Vault
from aww.settings import Settings

settings: Settings | None = None
engine: Engine
vault: Vault
journal: Journal


def initialize():
    """Initialize the module."""
    global settings, engine, vault, journal
    if settings is None:
        settings = Settings()
    engine = create_engine(settings.sqlite_url)
    vault = Vault(settings.obsidian.vault)
    journal = vault.journal()
