from datetime import date, time, timedelta
from aww.datastore.models import Event


def test_event_as_string():
    event = Event(date=date.today(), time=time(13, 0), text="aww")
    assert event.as_string() == "13:00 aww"
    event2 = Event(
        date=date.today(), time=time(13, 0), duration=timedelta(hours=1), text="aww 2"
    )
    assert event2.as_string() == "13:00 - 14:00 aww 2"


def test_event_from_string():
    dt = date.today()
    assert Event.from_string("08:30 aww", dt) == Event(
        date=date.today(), time=time(8, 30), duration=None, text="aww"
    )
    assert Event.from_string("08:30-09:30 aww", dt) == Event(
        date=date.today(), time=time(8, 30), duration=timedelta(hours=1), text="aww"
    )
    assert Event.from_string("08:30 - 09:30  aww", dt) == Event(
        date=date.today(), time=time(8, 30), duration=timedelta(hours=1), text="aww"
    )
