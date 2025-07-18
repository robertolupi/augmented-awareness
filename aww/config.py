from os.path import expanduser

from pydantic import DirectoryPath, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # The root path of the notes vault
    vault_path: DirectoryPath = Field(
        default_factory=lambda: expanduser('~/data/notes')
    )

    # The section within the daily files that holds journal notes and events
    journal_section: str = "Journal and events"

    # The directory inside the vault that holds the journal files
    journal_dir: str = "journal"
    
    # The directory inside the vault that holds retrospectives
    retrospectives_dir: str = "retrospectives"

    # Path to store cached data (e.g., generated retrospectives)
    data_path: DirectoryPath = Field(
        default_factory=lambda: expanduser('~/.cache/journal')
    )
    
    model_config = SettingsConfigDict(env_prefix='JOURNAL_', yaml_file=expanduser('~/.journal'))
