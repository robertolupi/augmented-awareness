from datetime import datetime, timedelta
import pyarrow as pa

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
    mock_client = mocker.patch(
        "aww.observe.activitywatch.ActivityWatchClient",
        return_value=mocker.Mock(
            get_buckets=mocker.Mock(return_value={"afk_bucket": {"type": "afkstatus"}}),
            get_events=mocker.Mock(
                return_value=[
                    Event(
                        timestamp=datetime(2025, 3, 25, 4, 54, 20, 101000),
                        duration=timedelta(seconds=1627, microseconds=632556),
                        data={"status": "afk"}
                    )
                ]
            )
        )
    )
    activity_watch = ActivityWatch()
    result = activity_watch.get_afk()
    assert isinstance(result, pa.Table)
    assert result.schema == pa.schema([
        pa.field("timestamp", pa.timestamp("s")),
        pa.field("duration", pa.duration("s")),
        pa.field("afk", pa.bool_())
    ])
    assert result["timestamp"][0].as_py() == datetime(2025, 3, 25, 4, 54, 20)
    assert result["duration"][0].as_py() == timedelta(seconds=1627)
    assert result["afk"][0].as_py() == True


def test_get_currentwindow(mocker):
    mock_client = mocker.patch(
        "aww.observe.activitywatch.ActivityWatchClient",
        return_value=mocker.Mock(
            get_buckets=mocker.Mock(return_value={"window_bucket": {"type": "currentwindow"}}),
            get_events=mocker.Mock(
                return_value=[
                    Event(
                        timestamp=datetime(2025, 4, 1, 8, 14, 40, 896000),
                        duration=timedelta(seconds=2, microseconds=795000),
                        data={"title": "Home", "app": "Arc"}
                    )
                ]
            )
        )
    )
    activity_watch = ActivityWatch()
    result = activity_watch.get_currentwindow()
    assert isinstance(result, pa.Table)
    assert result.schema == pa.schema([
        pa.field("timestamp", pa.timestamp("s")),
        pa.field("duration", pa.duration("s")),
        pa.field("title", pa.string()),
        pa.field("app", pa.dictionary(pa.int16(), pa.string()))
    ])
    assert result["timestamp"][0].as_py() == datetime(2025, 4, 1, 8, 14, 40)
    assert result["duration"][0].as_py() == timedelta(seconds=2)
    assert result["title"][0].as_py() == "Home"
    assert result["app"][0].as_py() == "Arc"


def test_get_web_history(mocker):
    mock_client = mocker.patch(
        "aww.observe.activitywatch.ActivityWatchClient",
        return_value=mocker.Mock(
            get_buckets=mocker.Mock(return_value={"web_bucket": {"type": "web.tab.current"}}),
            get_events=mocker.Mock(
                return_value=[
                    Event(
                        timestamp=datetime(2025, 2, 24, 18, 43, 39, 815000),
                        duration=timedelta(seconds=14, microseconds=285000),
                        data={
                            "url": "https://hallodeutschschule.ch/en/",
                            "title": "German Course in Zurich - Learn German at Hallo Deutschschule",
                            "audible": False,
                            "incognito": False
                        }
                    )
                ]
            )
        )
    )
    activity_watch = ActivityWatch()
    result = activity_watch.get_web_history()
    assert isinstance(result, pa.Table)
    assert result.schema == pa.schema([
        pa.field("timestamp", pa.timestamp("s")),
        pa.field("duration", pa.duration("s")),
        pa.field("title", pa.string()),
        pa.field("url", pa.string()),
        pa.field("incognito", pa.bool_()),
        pa.field("audible", pa.bool_())
    ])
    assert result["timestamp"][0].as_py() == datetime(2025, 2, 24, 18, 43, 39)
    assert result["duration"][0].as_py() == timedelta(seconds=14)
    assert result["title"][0].as_py() == "German Course in Zurich - Learn German at Hallo Deutschschule"
    assert result["url"][0].as_py() == "https://hallodeutschschule.ch/en/"
    assert result["incognito"][0].as_py() == False
    assert result["audible"][0].as_py() == False



