from datetime import date
from pathlib import PosixPath

import aww
from aww import obsidian
from aww.obsidian import Level

test_vault_path = (PosixPath(aww.__file__).parent.parent / 'test_vault').absolute()

def test_vault():
    vault = obsidian.Vault(test_vault_path, '.')
    assert vault.path == test_vault_path
    assert vault.journal_dir == '.'
    assert vault.path.exists()
    
    
def test_daily_page():
    vault = obsidian.Vault(test_vault_path, 'journal')
    page = vault.daily_page(date(2025, 3, 30))
    assert page.path.absolute() == (test_vault_path / 'journal/2025/03/2025-03-30.md').absolute()
    assert page.path.exists()
    assert page


def test_page():
    vault = obsidian.Vault(test_vault_path, 'journal')
    page1 = obsidian.Page(test_vault_path / 'journal/2025/03/2025-03-30.md', Level.daily)
    page2 = obsidian.Page(test_vault_path / 'journal/2025/04/2025-04-01.md', Level.daily)
    assert page1 != page2
    assert hash(page1) != hash(page2)