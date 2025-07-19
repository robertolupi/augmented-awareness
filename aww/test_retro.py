import asyncio
from pathlib import PosixPath
import shutil
import datetime
import pytest

from pydantic_ai.models.test import TestModel

import aww
from aww import retro
from aww.obsidian import Vault, Level
from aww.retro import RecursiveRetrospectiveGenerator

test_vault_path = (PosixPath(aww.__file__).parent.parent / 'test_vault').absolute()


@pytest.fixture
def tmp_vault(tmp_path):
    """Copy test_vault_path contents into a temporary directory."""
    dest = tmp_path / "vault"
    shutil.copytree(test_vault_path, dest)
    return Vault(PosixPath(dest), 'journal', 'retrospectives')


def days_between(start_year, start_month, start_day, end_year, end_month, end_day):
    """Return dates between start_year and end_year."""
    start = datetime.date(start_year, start_month, start_day)
    end = datetime.date(end_year, end_month, end_day)
    for d in range((end - start).days + 1):
        yield start + datetime.timedelta(days=d)


def test_build_retrospective_tree(tmp_vault):
    days_in_year = list(days_between(2025, 1, 1,
                                     2025, 12, 31))
    tree = retro.build_retrospective_tree(tmp_vault, days_in_year)
    assert len(tree) == 365 + 52 + 12 + 1

    one_day = datetime.date(2025, 1, 1)
    daily = tmp_vault.retrospective_daily_page(one_day)
    assert tree[daily].retro_page == daily
    assert set(tree[daily].dates) == {one_day}
    assert tree[daily].level == Level.daily
    assert len(tree[daily].sources) == 0  # no other retrospective pages

    january = list(days_between(2025, 1, 1,
                                2025, 1, 31))
    monthly = tmp_vault.retrospective_monthly_page(january[0])
    assert tree[monthly].retro_page == monthly
    assert set(tree[monthly].dates) == set(january)
    assert tree[monthly].level == Level.monthly
    assert len(tree[monthly].sources) == 31 + 5

    yearly = tmp_vault.retrospective_yearly_page(days_in_year[0])
    assert tree[yearly].retro_page == yearly
    assert set(tree[yearly].dates) == set(days_in_year)
    assert tree[yearly].level == Level.yearly
    assert len(tree[yearly].sources) == len(tree) - 1


class RecursiveRetrospectiveGeneratorForTesting(retro.RecursiveRetrospectiveGenerator):
    def __init__(self, vault: Vault, days: list[datetime.date], level: Level):
        model = TestModel()
        super().__init__(model, vault, days, level)
        self.saved_nodes = {}

    async def save_retro_page(self, node, output, sources, levels):
        await super().save_retro_page(node, output, sources, levels)
        self.saved_nodes[node.retro_page] = (node, sources, levels)


def test_recursive_retrospective_generator(tmp_vault):
    days_in_year = list(days_between(2025, 1, 1,
                                     2025, 12, 31))
    g = RecursiveRetrospectiveGeneratorForTesting(tmp_vault, days_in_year, Level.yearly)
    asyncio.run(g.run(0, list(Level)))
    yearly = tmp_vault.retrospective_yearly_page(days_in_year[0])
    
    march30 = datetime.date(2025, 3, 30)
    april1 = datetime.date(2025, 4, 1)
    d1 = tmp_vault.retrospective_daily_page(march30)
    d2 = tmp_vault.retrospective_daily_page(april1)
    w1 = tmp_vault.retrospective_weekly_page(march30)
    w2 = tmp_vault.retrospective_weekly_page(april1)
    march = tmp_vault.retrospective_monthly_page(march30)
    april = tmp_vault.retrospective_monthly_page(april1)
    
    sources_with_content = set(g.saved_nodes.keys())
    assert sources_with_content == {d1, d2, w1, w2, march, april, yearly}

    node, sources, levels = g.saved_nodes[yearly]
    assert node.retro_page == yearly
    assert levels == set(Level)
    source_pages = set(s.retro_page for s in sources)
    assert len(source_pages) == 365 + 52 + 12
