import collections
import datetime
from typing import Iterable, Callable, Tuple

import pyarrow as pa
from aw_client import ActivityWatchClient

from aww.settings import Settings


def _events_to_pyarrow(
    events: list[dict], *fields: tuple[pa.Field, Callable]
) -> pa.Table:
    timestamp_array = []
    duration_array = []
    data_arrays = collections.OrderedDict()
    for f, _ in fields:
        data_arrays[f.name] = []
    for event in events:
        timestamp_array.append(event.timestamp)
        duration_array.append(event.duration)
        for f, convert in fields:
            data_arrays[f.name].append(convert(event.data))
    return pa.Table.from_arrays(
        arrays=[timestamp_array, duration_array] + list(data_arrays.values()),
        schema=(
            pa.schema(
                [
                    pa.field("timestamp", pa.timestamp("s")),
                    pa.field("duration", pa.duration("s")),
                ]
                + list(f for f, _ in fields)
            )
        ),
    )


class ActivityWatch:
    """Observe user activity via ActivityWatch."""

    client: ActivityWatchClient

    def __init__(
        self, client_name: str | None = None, client: ActivityWatchClient | None = None
    ):
        self.client = client or ActivityWatchClient(
            client_name or Settings().activitywatch.client_name
        )

    def get_buckets_by_type(self, type_name: str) -> Iterable[str]:
        """Get the bucket IDs by type of bucket."""
        buckets = self.client.get_buckets()
        for bucket_id, bucket_dict in buckets.items():
            if bucket_dict["type"] == type_name:
                yield bucket_id

    def get_events(
        self,
        bucket: str,
        start: datetime.datetime | None = None,
        end: datetime.datetime | None = None,
        *fields: tuple[pa.Field, Callable],
    ) -> pa.Table:
        events = self.client.get_events(bucket, start=start, end=end)
        return _events_to_pyarrow(events, *fields)

    def query(
        self,
        query: str,
        timeperiods: list[Tuple[datetime.datetime, datetime.datetime]],
        name: str,
        *fields: tuple[pa.Field, Callable],
    ) -> pa.Table:
        events = self.client.query(query, timeperiods, name)
        return _events_to_pyarrow(events, *fields)

    def get_afk(
        self,
        start: datetime.datetime | None = None,
        end: datetime.datetime | None = None,
    ) -> pa.Table:
        # Example:
        # {'id': 76392,
        #  'timestamp': datetime.datetime(2025, 3, 25, 4, 54, 20, 101000, tzinfo=datetime.timezone.utc),
        #  'duration': datetime.timedelta(seconds=1627, microseconds=632556),
        #  'data': {'status': 'afk'}},
        bucket = next(self.get_buckets_by_type("afkstatus"))
        return self.get_events(
            bucket,
            start,
            end,
            (pa.field("afk", pa.bool_()), lambda data: data["status"] == "afk"),
        )

    def get_currentwindow(
        self,
        start: datetime.datetime | None = None,
        end: datetime.datetime | None = None,
    ):
        # Example:
        # {'id': 96028,
        #  'timestamp': datetime.datetime(2025, 4, 1, 8, 14, 40, 896000, tzinfo=datetime.timezone.utc),
        #  'duration': datetime.timedelta(seconds=2, microseconds=795000),
        #  'data': {'title': 'Home', 'app': 'Arc'}},
        bucket = next(self.get_buckets_by_type("currentwindow"))
        return self.get_events(
            bucket,
            start,
            end,
            (pa.field("title", pa.string()), lambda data: data["title"]),
            (
                pa.field("app", pa.dictionary(pa.int16(), pa.string())),
                lambda data: data["app"],
            ),
        )

    def get_web_history(
        self,
        start: datetime.datetime | None = None,
        end: datetime.datetime | None = None,
    ):
        bucket = next(self.get_buckets_by_type("web.tab.current"))
        # Example:
        # {'id': 28001,
        #  'timestamp': datetime.datetime(2025, 2, 24, 18, 43, 39, 815000, tzinfo=datetime.timezone.utc),
        #  'duration': datetime.timedelta(seconds=14, microseconds=285000),
        #  'data': {'url': 'https://hallodeutschschule.ch/en/',
        #           'title': 'German Course in Zurich - Learn German at Hallo Deutschschule',
        #           'audible': False,
        #           'incognito': False,
        #           'tabCount': 68}},
        return self.get_events(
            bucket,
            start,
            end,
            (pa.field("title", pa.string()), lambda data: data["title"]),
            (pa.field("url", pa.string()), lambda data: data["url"]),
            (pa.field("incognito", pa.bool_()), lambda data: data["incognito"]),
            (pa.field("audible", pa.bool_()), lambda data: data["audible"]),
        )
