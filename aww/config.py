from os.path import expanduser

from pydantic import DirectoryPath, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    vault_path : DirectoryPath = Field(alias="vault_path", default=DirectoryPath(expanduser('~/data/notes')))
    
    # The section within the daily files that holds journal notes and events
    journal_section : str = Field(alias="journal_section", default="Journal and events")
    
    # The directory inside the vault that hold the journal files
    journal_dir : str = Field(alias="journal_dir", default="journal")
    
    data_path : DirectoryPath = Field(alias="data_path", default=DirectoryPath(expanduser('~/.cache/journal')))
    
    model_config = SettingsConfigDict(env_prefix='JOURNAL_', yaml_file=expanduser('~/.journal'))
