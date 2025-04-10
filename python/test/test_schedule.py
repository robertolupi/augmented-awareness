import datetime
import pathlib

import aww.settings
from aww.observe.obsidian import Vault
from aww.orient.schedule import Schedule

test_dir = pathlib.Path(__file__).parent
test_vault_dir = test_dir / "vault"
aww.settings.CONFIG_FILE = test_dir / "config.toml"


def test_schedule():
    date_start = datetime.date(2025, 3, 1)
    date_end = datetime.date(2025, 3, 31)
    schedule = Schedule(Vault(test_vault_dir).journal().subrange(date_start, date_end))
    assert datetime.date(2025, 3, 30) in schedule.journal
    assert datetime.date(2025, 4, 1) not in schedule.journal


def test_total_duration_by_tag():
    date_start = datetime.date(2025, 3, 1)
    date_end = datetime.date(2025, 4, 1)
    schedule = Schedule(Vault(test_vault_dir).journal().subrange(date_start, date_end))
    table = schedule.total_duration_by_tag().sort_by("tag")
    assert table["tag"].to_pylist() == ["aww", "create/write/blog", "work"]
    assert table["duration"].to_pylist() == [
        datetime.timedelta(seconds=90 * 60),
        datetime.timedelta(seconds=120 * 60),
        datetime.timedelta(seconds=7 * 60 * 60),
    ]
    # TODO: test histogram
