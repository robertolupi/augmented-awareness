from dataclasses import dataclass
from typing import Optional

from aww.obsidian import Vault
from aww.rag import Index


@dataclass
class ChatDeps:
    vault: Vault
    index: Optional[Index] = None
