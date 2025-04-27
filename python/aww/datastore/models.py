from datetime import datetime, date, time, timedelta
from sqlmodel import SQLModel, Field
from typing import Optional


class Event(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    date: date
    time: time
    duration: Optional[timedelta]
    text: str

    def as_string(self):
        start = datetime.combine(self.date, self.time)
        end = start + self.duration if self.duration else None
        return (
            f"{start:%H:%M} - {end:%H:%M} {self.text}"
            if self.duration
            else f"{start:%H:%M} {self.text}"
        )

    def __str__(self):
        return f"{self.date} {self.as_string()}"

    def __rich__(self):
        return self.as_string()
