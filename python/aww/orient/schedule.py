import collections
from datetime import datetime, timedelta

import pyarrow as pa

from aww.observe.obsidian import Vault, Journal


class Schedule:
    journal: Journal

    def __init__(
        self,
        journal : Journal | None = None,    
    ):
        self.journal = journal or Vault().journal()

    def __repr__(self):
        return f"Schedule({self.journal})"

    def tasks_table(self) -> pa.Table:
        name_list = []
        done_list = []
        created_list = []
        due_list = []
        started_list = []
        scheduled_list = []
        recurrence_list = []

        for page in self.journal.values():
            for task in page.tasks():
                name_list.append(task.name)
                done_list.append(task.done)
                created_list.append(task.created)
                due_list.append(task.due)
                started_list.append(task.started)
                scheduled_list.append(task.scheduled)
                recurrence_list.append(task.recurrence)

        return pa.Table.from_arrays(
            arrays=[
                pa.array(name_list),
                pa.array(done_list),
                pa.array(created_list),
                pa.array(due_list),
                pa.array(started_list),
                pa.array(scheduled_list),
                pa.array(recurrence_list),
            ],
            schema=pa.schema(
                [
                    pa.field("name", pa.string()),
                    pa.field("done", pa.bool_()),
                    pa.field("created", pa.date32()),
                    pa.field("due", pa.date32()),
                    pa.field("started", pa.date32()),
                    pa.field("scheduled", pa.date32()),
                    pa.field("recurrence", pa.string()),
                ]
            ),
        )

    def event_table(self) -> pa.Table:
        name_list = []
        time_list = []
        tags_list = []
        durations_list = []
        for page in self.journal.values():
            for event in page.events():
                name_list.append(event.name)
                time_list.append(event.time)
                tags_list.append(event.tags)
                durations_list.append(event.duration)
        return pa.Table.from_arrays(
            arrays=[
                pa.array(name_list),
                pa.array(time_list),
                pa.array(tags_list),
                pa.array(durations_list),
            ],
            schema=pa.schema(
                [
                    pa.field("name", pa.string()),
                    pa.field("time", pa.timestamp("s")),
                    pa.field("tags", pa.list_(pa.dictionary(pa.int64(), pa.string()))),
                    pa.field("duration", pa.duration("s")),
                ]
            ),
        )

    def total_duration_by_tag(self) -> pa.Table:
        totals = collections.defaultdict(lambda: timedelta(seconds=0))
        for page in self.journal.values():
            for event in page.events():
                for tag in event.tags:
                    if event.duration is not None:
                        totals[tag] += event.duration
        tag_list = list(totals.keys())
        duration_list = list(totals.values())
        tag_durations = pa.Table.from_arrays(
            [pa.array(tag_list), pa.array(duration_list)],
            schema=pa.schema(
                [pa.field("tag", pa.string()), pa.field("duration", pa.duration("s"))]
            ),
        )
        return tag_durations.sort_by([("duration", "descending")])
