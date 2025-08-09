from pathlib import Path
import shutil
import datetime
import pytest

import aww
import aww.obsidian
import aww.retro
from aww.obsidian import Vault, Level

test_vault_path = (Path(aww.__file__).parent.parent / "test_vault").absolute()


@pytest.fixture
def tmp_vault(tmp_path):
    """Copy test_vault_path contents into a temporary directory."""
    dest = tmp_path / "vault"
    shutil.copytree(test_vault_path, dest)
    return Vault(Path(dest), "journal", "retrospectives")


def days_between(start_year, start_month, start_day, end_year, end_month, end_day):
    """Return dates between start_year and end_year."""
    start = datetime.date(start_year, start_month, start_day)
    end = datetime.date(end_year, end_month, end_day)
    for d in range((end - start).days + 1):
        yield start + datetime.timedelta(days=d)


def test_build_retrospective_tree(tmp_vault):
    days_in_year = list(days_between(2025, 1, 1, 2025, 12, 31))
    tree = aww.retro.build_retrospective_tree(tmp_vault, days_in_year)
    assert len(tree) == 365 + 52 + 12 + 1

    one_day = datetime.date(2025, 1, 1)
    daily = tmp_vault.retrospective_page(one_day, Level.daily)
    assert tree[daily].retro_page == daily
    assert set(tree[daily].dates) == {one_day}
    assert tree[daily].level == Level.daily
    assert len(tree[daily].sources) == 0  # no other retrospective pages

    january = list(days_between(2025, 1, 1, 2025, 1, 31))
    d = january[0]
    monthly = tmp_vault.retrospective_page(d, Level.monthly)
    assert tree[monthly].retro_page == monthly
    assert set(tree[monthly].dates) == set(january)
    assert tree[monthly].level == Level.monthly
    assert len(tree[monthly].sources) == 31 + 5

    d1 = days_in_year[0]
    yearly = tmp_vault.retrospective_page(d1, Level.yearly)
    assert tree[yearly].retro_page == yearly
    assert set(tree[yearly].dates) == set(days_in_year)
    assert tree[yearly].level == Level.yearly
    assert len(tree[yearly].sources) == len(tree) - 1
