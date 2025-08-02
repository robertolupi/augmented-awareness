import asyncio
from pathlib import Path
import shutil
import datetime
import pytest

from pydantic_ai.models.test import TestModel

import aww
import aww.obsidian
from aww import retro
from aww.obsidian import Vault, Level
from aww.retro import RecursiveRetrospectiveGenerator

test_vault_path = (Path(aww.__file__).parent.parent / 'test_vault').absolute()


@pytest.fixture
def tmp_vault(tmp_path):
    """Copy test_vault_path contents into a temporary directory."""
    dest = tmp_path / "vault"
    shutil.copytree(test_vault_path, dest)
    return Vault(Path(dest), 'journal', 'retrospectives')


def days_between(start_year, start_month, start_day, end_year, end_month, end_day):
    """Return dates between start_year and end_year."""
    start = datetime.date(start_year, start_month, start_day)
    end = datetime.date(end_year, end_month, end_day)
    for d in range((end - start).days + 1):
        yield start + datetime.timedelta(days=d)


def test_build_retrospective_tree(tmp_vault):
    days_in_year = list(days_between(2025, 1, 1,
                                     2025, 12, 31))
    tree = aww.obsidian.build_retrospective_tree(tmp_vault, days_in_year)
    assert len(tree) == 365 + 52 + 12 + 1

    one_day = datetime.date(2025, 1, 1)
    daily = tmp_vault.retrospective_page(one_day, Level.daily)
    assert tree[daily].retro_page == daily
    assert set(tree[daily].dates) == {one_day}
    assert tree[daily].level == Level.daily
    assert len(tree[daily].sources) == 0  # no other retrospective pages

    january = list(days_between(2025, 1, 1,
                                2025, 1, 31))
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


class RecursiveRetrospectiveGeneratorForTesting(retro.RecursiveRetrospectiveGenerator):
    def __init__(self, vault: Vault, days: list[datetime.date], level: Level):
        model = TestModel()
        super().__init__(model, vault, days, level)
        self.saved_nodes = {}

    async def save_retro_page(self, node, output, sources, levels, retro_frontmatter):
        await super().save_retro_page(node, output, sources, levels, retro_frontmatter)
        self.saved_nodes[node.retro_page] = (node, sources, levels)


def test_recursive_retrospective_generator(tmp_vault):
    days_in_year = list(days_between(2025, 1, 1,
                                     2025, 12, 31))
    g = RecursiveRetrospectiveGeneratorForTesting(tmp_vault, days_in_year, Level.yearly)
    asyncio.run(g.run(context_levels=list(Level),
                      cache_policies=[retro.NoRootCachePolicy(), retro.NoLevelsCachePolicy(list(Level))]))
    d = days_in_year[0]
    yearly = tmp_vault.retrospective_page(d, Level.yearly)

    march30 = datetime.date(2025, 3, 30)
    april1 = datetime.date(2025, 4, 1)
    d1 = tmp_vault.retrospective_page(march30, Level.daily)
    d2 = tmp_vault.retrospective_page(april1, Level.daily)
    w1 = tmp_vault.retrospective_page(march30, Level.weekly)
    w2 = tmp_vault.retrospective_page(april1, Level.weekly)
    march = tmp_vault.retrospective_page(march30, Level.monthly)
    april = tmp_vault.retrospective_page(april1, Level.monthly)

    sources_with_content = set(g.saved_nodes.keys())
    assert sources_with_content == {d1, d2, w1, w2, march, april, yearly}

    node, sources, levels = g.saved_nodes[yearly]
    assert node.retro_page == yearly
    assert levels == set(Level)
    source_pages = set(s.retro_page for s in sources)
    assert len(source_pages) == 365 + 52 + 12

def test_recursive_retrospective_generator_rename_on_disk(tmp_vault):
    day = datetime.date(2025, 1, 1)
    model = TestModel()

    # Create a dummy journal file for the day
    journal_path = tmp_vault.path / tmp_vault.journal_dir / f"{day.strftime('%Y')}/{day.strftime('%m')}/{day.strftime('%Y-%m-%d')}.md"
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with journal_path.open("w") as f:
        f.write("# Test Journal Entry")

    g = RecursiveRetrospectiveGenerator(model, tmp_vault, [day], Level.daily)

    # Run the generator twice
    asyncio.run(g.run(context_levels=list(Level),
                      cache_policies=[retro.NoRootCachePolicy(), retro.NoLevelsCachePolicy(list(Level))]))
    asyncio.run(g.run(context_levels=list(Level),
                      cache_policies=[retro.NoRootCachePolicy(), retro.NoLevelsCachePolicy(list(Level))]))

    retro_page = tmp_vault.retrospective_page(day, Level.daily)
    renamed_page_path = retro_page.path.with_suffix('.1.md')

    assert retro_page.path.exists()
    assert renamed_page_path.exists()