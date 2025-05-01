from datetime import datetime, date, time, timedelta
from sqlmodel import SQLModel, Field
from sqlalchemy.types import JSON
from typing import Optional
import re

EVENT_RE = re.compile(
    r"(?P<time>\d{1,2}:\d{2})(\s*-\s*(?P<end_time>\d{1,2}:\d{2}))?\s+(?P<name>.+)$"
)


class Event(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    date: date
    time: time
    duration: Optional[timedelta]
    text: str
    tags: list[str] = Field(default=[], sa_type=JSON)

    def __init__(self, **data):
        super().__init__(**data)
        self.tags = [t[1:].lower() for t in self.text.split() if t.startswith("#")]

    def as_string(self):
        start = datetime.combine(self.date, self.time)
        end = start + self.duration if self.duration else None
        return (
            f"{start:%H:%M} - {end:%H:%M} {self.text}"
            if self.duration
            else f"{start:%H:%M} {self.text}"
        )

    @classmethod
    def from_string(cls, text: str, dt: date):
        """Parse an event from a string in the format "HH:MM text" or "HH:MM-HH:MM text"""
        m = EVENT_RE.match(text)
        if not m:
            raise ValueError(f"Invalid event string: {text}")
        start = time.fromisoformat(m.group("time"))
        if m.group("end_time"):
            end = time.fromisoformat(m.group("end_time"))
            duration = datetime.combine(dt, end) - datetime.combine(dt, start)
        else:
            duration = None
        return cls(date=dt, time=start, duration=duration, text=m.group("name"))

    def __str__(self):
        return f"{self.date} {self.as_string()}"

    def __rich__(self):
        return self.as_string()
