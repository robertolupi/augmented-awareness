import datetime
from typing import Iterable

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

    def get_afk(
        self,
        bucket_id: str | None = None,
        start: datetime.datetime | None = None,
        end: datetime.datetime | None = None,
    ) -> pa.Table:
        if bucket_id is None:
            buckets = list(self.get_buckets_by_type("afkstatus"))
            if len(buckets) != 1:
                raise ValueError(f"Expecting one afkstatus buckets, got: {buckets}")
            bucket_id = buckets[0]

        events = self.client.get_events(bucket_id, start=start, end=end)
        timestamp_arr = []
        duration_arr = []
        status_arr = []
        for event in events:
            timestamp_arr.append(event.timestamp)
            duration_arr.append(event.duration)
            status_arr.append(event.data["status"] == "afk")
        return pa.Table.from_arrays(
            arrays=[timestamp_arr, duration_arr, status_arr],
            schema=pa.schema(
                [
                    pa.field("timestamp", pa.timestamp("s")),
                    pa.field("duration", pa.duration("s")),
                    pa.field("afk", pa.bool_()),
                ]
            ),
        )
