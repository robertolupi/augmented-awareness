import math
import re
from datetime import timedelta, time, date
from typing import Iterable, Dict
from collections import OrderedDict

import pyarrow as pa

from aww.observe.obsidian import Vault, Journal


class Schedule:
    journal: Journal

    def __init__(self, journal: Journal | None = None):
        self.journal = journal or Vault().journal()

    def __repr__(self):
        return f"Schedule({self.journal})"

    def read_schedule(self, header_re: re.Pattern | str) -> Dict[date, str]:
        result = OrderedDict()
        for d, page in self.journal.items():
            result[d] = page.get_section(header_re)
        return result

    def total_duration_by_tag(
        self, histogram_resolution: timedelta = timedelta(minutes=30)
    ) -> pa.Table:
        """
        Calculates the total duration spent on events for each tag and
        generates a time-of-day histogram for tag occurrences.

        Args:
            histogram_resolution: The time duration each histogram bucket represents.
                                  Defaults to 30 minutes.

        Returns:
            A PyArrow Table sorted by duration descending, containing:
            - 'tag': The tag string.
            - 'duration': The total duration associated with the tag.
            - 'histogram': A list representing the count of events starting
                           within each time bucket across a 24-hour period.
        """
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
    """
    Determines which histogram bins an event falls into based on its start time and duration.

    Args:
        start_time: The time the event started.
        duration: The duration of the event. If None, it defaults to the size of one bin.
        n_buckets: The total number of bins dividing a 24-hour period.

    Yields:
        The index of each bin the event overlaps with.
    """
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
