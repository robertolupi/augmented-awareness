import collections
import datetime
from typing import Iterable, Callable

import pyarrow as pa
from aw_client import ActivityWatchClient

from aww.settings import Settings


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

    def get_events(self, bucket: str, start: datetime.datetime | None = None, end: datetime.datetime | None = None,
                   *fields: tuple[pa.Field, Callable]):
        events = self.client.get_events(bucket, start=start, end=end)
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
            schema=(pa.schema([
                                  pa.field("timestamp", pa.timestamp("s")),
                                  pa.field("duration", pa.duration("s")),
                              ] + list(f for f, _ in fields))),
        )

    def get_afk(
            self,
            start: datetime.datetime | None = None,
            end: datetime.datetime | None = None,
    ) -> pa.Table:
        bucket = next(self.get_buckets_by_type("afkstatus"))
        return self.get_events(bucket, start, end,
                               (pa.field("afk", pa.bool_()), lambda data: data['status'] == "afk"))
