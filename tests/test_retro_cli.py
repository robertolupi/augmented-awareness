import datetime
from unittest.mock import MagicMock

import pytest

from aww import retro
from aww.cli.retro import NoCachePolicyChoice, get_cache_policies
from aww.obsidian import Level
from aww.test_retro import tmp_vault


def test_get_cache_policies_root():
    policies = get_cache_policies([NoCachePolicyChoice.ROOT])
    assert len(policies) == 1
    assert isinstance(policies[0], retro.NoRootCachePolicy)


def test_get_cache_policies_levels():
    policies = get_cache_policies([NoCachePolicyChoice.DAILY, NoCachePolicyChoice.WEEKLY])
    assert len(policies) == 1
    assert isinstance(policies[0], retro.NoLevelsCachePolicy)
    assert policies[0].levels == {Level.daily, Level.weekly}


def test_get_cache_policies_mixed():
    policies = get_cache_policies(
        [NoCachePolicyChoice.ROOT, NoCachePolicyChoice.MTIME, NoCachePolicyChoice.DAILY]
    )
    assert len(policies) == 3
    assert any(isinstance(p, retro.NoRootCachePolicy) for p in policies)
    assert any(isinstance(p, retro.ModificationTimeCachePolicy) for p in policies)
    assert any(isinstance(p, retro.NoLevelsCachePolicy) for p in policies)


def test_retro_cli_missing_daily_note(tmp_vault, capsys):
    import click
    from pydantic_ai.models.test import TestModel
    from aww.cli.retro import retrospectives

    with click.Context(retrospectives, obj={"vault": tmp_vault, "llm_model": TestModel()}) as ctx:
        ctx.invoke(
            retrospectives,
            level=Level.daily,
            date=datetime.datetime(2025, 1, 15),
            no_cache=[],
            context=[],
            concurrency_limit=None,
            yesterday=False,
            output_file=None,
            plain_text=False,
        )
    captured = capsys.readouterr()
    assert "Missing daily journal file for 2025-01-15" in captured.out



