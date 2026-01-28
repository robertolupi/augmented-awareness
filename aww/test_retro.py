import datetime
import shutil
from pathlib import Path

import pytest

import aww
import aww.obsidian
import aww.retro
from aww.obsidian import Level, Vault
from aww.retro import Selection, whole_month, whole_week

test_vault_path = (Path(aww.__file__).parent.parent / "test_vault").absolute()


@pytest.fixture
def tmp_vault(tmp_path):
    """Copy test_vault_path contents into a temporary directory."""
    dest = tmp_path / "vault"
    shutil.copytree(test_vault_path, dest)
    return Vault(Path(dest), "journal", "retrospectives", "retrospectives/queries")


def days_between(start_year, start_month, start_day, end_year, end_month, end_day):
    """Return dates between start_year and end_year."""
    start = datetime.date(start_year, start_month, start_day)
    end = datetime.date(end_year, end_month, end_day)
    for d in range((end - start).days + 1):
        yield start + datetime.timedelta(days=d)


def test_build_retrospective_tree(tmp_vault):
    days_in_year = list(days_between(2025, 1, 1, 2025, 12, 31))
    tree = aww.retro.build_retrospective_tree(tmp_vault, days_in_year)
    # 2025 has 53 ISO weeks
    assert len(tree) == 365 + 53 + 12 + 1

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


def _expected_tree_size(vault: Vault, dates: list[datetime.date]) -> int:
    """Compute expected unique nodes in the tree for the given dates."""
    daily = {vault.retrospective_page(d, Level.daily) for d in dates}
    weekly = {vault.retrospective_page(d, Level.weekly) for d in dates}
    monthly = {vault.retrospective_page(d, Level.monthly) for d in dates}
    yearly = {vault.retrospective_page(d, Level.yearly) for d in dates}
    return len(daily | weekly | monthly | yearly)


def test_selection_daily(tmp_vault):
    # Use a date present in test_vault
    d = datetime.date(2025, 4, 1)
    sel = Selection(tmp_vault, d, Level.daily)

    assert sel.dates == [d]
    assert sel.root.level == Level.daily
    assert sel.root.dates == {d}
    assert len(sel.root.sources) == 0

    # Tree should contain one node per (daily, weekly, monthly, yearly) for that date
    assert len(sel.tree) == _expected_tree_size(tmp_vault, [d])

    # Inspect other levels for correct source wiring
    weekly_node = sel.tree[tmp_vault.retrospective_page(d, Level.weekly)]
    monthly_node = sel.tree[tmp_vault.retrospective_page(d, Level.monthly)]
    yearly_node = sel.tree[tmp_vault.retrospective_page(d, Level.yearly)]

    assert len(weekly_node.sources) == 1  # daily
    assert len(monthly_node.sources) == 2  # daily + weekly
    assert len(yearly_node.sources) == 3  # daily + weekly + monthly


def test_selection_weekly(tmp_vault):
    d = datetime.date(2025, 3, 30)  # Sunday; week spans Mon-Sun
    expected_week = whole_week(d)
    sel = Selection(tmp_vault, d, Level.weekly)

    assert sel.root.level == Level.weekly
    assert set(sel.root.dates) == set(expected_week)
    assert len(sel.tree) == _expected_tree_size(tmp_vault, expected_week)

    # Weekly root should depend on all daily nodes of the week
    daily_pages = {tmp_vault.retrospective_page(x, Level.daily) for x in expected_week}
    daily_nodes = {sel.tree[p] for p in daily_pages}
    assert sel.root.sources == daily_nodes


def test_selection_monthly(tmp_vault):
    d = datetime.date(2025, 4, 1)
    expected_month = whole_month(d)
    sel = Selection(tmp_vault, d, Level.monthly)

    assert sel.root.level == Level.monthly
    assert set(sel.root.dates) == set(expected_month)
    assert len(sel.tree) == _expected_tree_size(tmp_vault, expected_month)

    # Monthly root should depend on all daily and weekly nodes in the month
    daily_pages = {tmp_vault.retrospective_page(x, Level.daily) for x in expected_month}
    weekly_pages = {
        tmp_vault.retrospective_page(x, Level.weekly) for x in expected_month
    }
    expected_sources = {sel.tree[p] for p in (daily_pages | weekly_pages)}
    assert sel.root.sources == expected_sources


def test_selection_apply_cache_policies(tmp_vault):
    d = datetime.date(2025, 3, 30)
    sel = Selection(tmp_vault, d, Level.weekly)

    # By default all nodes use cache
    assert all(n.use_cache for n in sel.tree.values())

    # Disable cache on root
    sel.apply_cache_policy(aww.retro.NoRootCachePolicy())
    assert sel.root.use_cache is False
    # Others remain unchanged
    assert all((n is sel.root) or n.use_cache for n in sel.tree.values())

    # Now disable cache on daily sources of the weekly root
    sel2 = Selection(tmp_vault, d, Level.weekly)
    sel2.apply_cache_policy(aww.retro.NoLevelsCachePolicy([Level.daily]))
    for n in sel2.root.sources:
        if n.level == Level.daily:
            assert n.use_cache is False
        else:
            assert n.use_cache is True
