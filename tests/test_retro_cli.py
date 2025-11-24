import datetime
from unittest.mock import MagicMock

import pytest

from aww import retro
from aww.cli.retro import NoCachePolicyChoice, get_cache_policies
from aww.obsidian import Level


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
