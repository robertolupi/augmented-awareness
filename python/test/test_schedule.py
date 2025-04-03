import datetime
import pathlib

import aww.settings
from aww.orient.schedule import Schedule

test_dir = pathlib.Path(__file__).parent
test_vault_dir = test_dir / "vault"
aww.settings.CONFIG_FILE = test_dir / "config.toml"


def test_schedule():
    date_start = datetime.date(2025, 3, 1)
    date_end = datetime.date(2025, 3, 31)
    schedule = Schedule(date_start, date_end)
    assert datetime.date(2025, 3, 30) in schedule.journal
    assert datetime.date(2025, 4, 1) not in schedule.journal


def test_event_table():
    date_start = datetime.date(2025, 3, 1)
    date_end = datetime.date(2025, 4, 1)
    schedule = Schedule(date_start, date_end)
    table = schedule.event_table()
    assert len(table) == 6
    assert table["name"].to_pylist() == [
        "wake up",
        "breakfast & shower",
        "yoga",
        "woke up",
        "#aww did some work",
        "#work",
    ]
    assert table["time"].to_pylist() == [
        datetime.datetime(2025, 3, 30, 6, 15),
        datetime.datetime(2025, 3, 30, 6, 30),
        datetime.datetime(2025, 3, 30, 7, 0),
        datetime.datetime(2025, 4, 1, 6, 4),
        datetime.datetime(2025, 4, 1, 7, 0),
        datetime.datetime(2025, 4, 1, 8, 30),
    ]
    assert table["tags"].to_pylist() == [[], [], [], [], ["aww"], ["work"]]
    assert table["duration"].to_pylist() == [
        datetime.timedelta(seconds=15 * 60),
        datetime.timedelta(seconds=30 * 60),
        None,
        datetime.timedelta(seconds=56 * 60),
        datetime.timedelta(seconds=90 * 60),
        None,
    ]


def test_total_duration_by_tag():
    date_start = datetime.date(2025, 3, 1)
    date_end = datetime.date(2025, 4, 1)
    schedule = Schedule(date_start, date_end)
    table = schedule.total_duration_by_tag()
    assert table["tag"].to_pylist() == ["aww"]
    assert table["duration"].to_pylist() == [
        datetime.timedelta(seconds=90 * 60),
    ]
