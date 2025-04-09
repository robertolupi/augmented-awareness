import math
from datetime import timedelta, time
from typing import Iterable

import pyarrow as pa

from aww.observe.obsidian import Vault, Journal, Task, Event
from aww.pyarrow_util import pydantic_to_pyarrow_schema


class Schedule:
    journal: Journal

    def __init__(self, journal: Journal | None = None):
        self.journal = journal or Vault().journal()

    def __repr__(self):
        return f"Schedule({self.journal})"

    def tasks_table(self) -> pa.Table:
        schema = pydantic_to_pyarrow_schema(Task)
        arrays = [[] for _ in schema.names]
        for page in self.journal.values():
            for task in page.tasks():
                for i, name in enumerate(schema.names):
                    arrays[i].append(getattr(task, name))
        return pa.Table.from_arrays(arrays=arrays, schema=schema)

    def event_table(self) -> pa.Table:
        schema = pydantic_to_pyarrow_schema(Event)
        arrays = [[] for _ in schema.names]
        for page in self.journal.values():
            for event in page.events():
                for i, name in enumerate(schema.names):
                    arrays[i].append(getattr(event, name))
        return pa.Table.from_arrays(arrays=arrays, schema=schema)

    def total_duration_by_tag(
        self, histogram_resolution: timedelta = timedelta(minutes=30)
    ) -> pa.Table:
        totals = {}
        histograms = {}
        n_buckets = int(
            math.ceil(
                timedelta(days=1).total_seconds() / histogram_resolution.total_seconds()
            )
        )
        for page in self.journal.values():
            for event in page.events():
                for tag in event.tags:
                    if tag not in totals:
                        totals[tag] = timedelta(seconds=0)
                        histograms[tag] = [0] * n_buckets
                    totals[tag] += event.duration or timedelta(seconds=0)
                    for n in histogram_bins(
                        event.time.time(), event.duration, n_buckets
                    ):
                        histograms[tag][n] += 1

        tag_list = list(totals.keys())
        duration_list = list(totals.values())
        histogram_list = list(histograms.values())
        tag_durations = pa.Table.from_arrays(
            [pa.array(tag_list), pa.array(duration_list), pa.array(histogram_list)],
            schema=pa.schema(
                [
                    pa.field("tag", pa.string()),
                    pa.field("duration", pa.duration("s")),
                    pa.field("histogram", pa.list_(pa.int64())),
                ]
            ),
        )
        return tag_durations.sort_by([("duration", "descending")])


def histogram_bins(
    start_time: time, duration: timedelta | None, n_buckets: int
) -> Iterable[int]:
    delta = timedelta(days=1) / n_buckets
    duration = duration or delta  # mark at least one bucket
    start = timedelta(
        hours=start_time.hour, minutes=start_time.minute, seconds=start_time.second
    )
    t = timedelta(seconds=0)
    for i in range(n_buckets):
        if start <= t < start + duration:
            yield i
        t += delta
