from datetime import datetime, timedelta

from aw_core.models import Event

from aww.observe.activitywatch import ActivityWatch


def test_activitywatch(mocker):
    mock_client = mocker.patch(
        "aww.observe.activitywatch.ActivityWatchClient", return_value=mocker.Mock()
    )
    ActivityWatch()
    mock_client.assert_called_once()


def test_bucket_id_by_type(mocker):
    mocker.patch(
        "aww.observe.activitywatch.ActivityWatchClient",
        return_value=mocker.Mock(
            get_buckets=mocker.Mock(
                return_value={
                    "bucket_id_1": {"type": "afk"},
                    "bucket_id_2": {"type": "afk"},
                }
            )
        ),
    )
    activity_watch = ActivityWatch()
    assert list(activity_watch.get_buckets_by_type("afk")) == [
        "bucket_id_1",
        "bucket_id_2",
    ]
    assert list(activity_watch.get_buckets_by_type("invalid")) == []


def test_get_afk(mocker):
    t1 = datetime(2025, 3, 1, 0, 0, 0)
    d1 = timedelta(seconds=10 * 60)
    t2 = t1 + d1
    d2 = timedelta(seconds=20 * 60)
    mocker.patch(
        "aww.observe.activitywatch.ActivityWatchClient",
        return_value=mocker.Mock(
            get_buckets=mocker.Mock(
                return_value={
                    "bucket_id_1": {"type": "afkstatus"},
                }
            ),
            get_events=mocker.Mock(
                return_value=[
                    Event(id=1, timestamp=t1, duration=d1, data={"status": "afk"}),
                    Event(id=2, timestamp=t2, duration=d2, data={"status": "not_afk"}),
                ]
            ),
        ),
    )
    activity_watch = ActivityWatch()
    table = activity_watch.get_afk()
    assert table.to_pylist() == [
        {"timestamp": t1, "duration": d1, "afk": True},
        {"timestamp": t2, "duration": d2, "afk": False},
    ]
