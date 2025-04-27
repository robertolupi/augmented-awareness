from datetime import datetime, time, date
import sys

import click
import rich
import rich.prompt
from sqlmodel import create_engine, SQLModel, Session, select, update

from aww import context

import aww.datastore.models  # noqa: F401

from aww.datastore.models import Event


@click.group(name="datastore")
def commands():
    """Manage the datastore."""
    pass


@commands.command()
def init():
    """Initialize the datastore."""
    settings = context.settings
    if settings.sqlite_db.exists():
        rich.print(f"[red]Database already exists at {settings.sqlite_db}[/red]")
        ok = rich.prompt.Confirm.ask("Do you want to overwrite it?", default=False)
        if not ok:
            sys.exit(1)
            return
        settings.sqlite_db.unlink()
    settings.sqlite_db.parent.mkdir(parents=True, exist_ok=True)
    rich.print(f"Creating database at {settings.sqlite_db}")
    engine = create_engine(settings.sqlite_url)
    SQLModel.metadata.create_all(engine)
    rich.print(f"Database created at [green]{settings.sqlite_db}[/green]")
    if not settings.data_path.exists():
        rich.print(f"Creating data directory at [green]{settings.data_path}[/green]")
        settings.data_path.mkdir(parents=True, exist_ok=True)
    else:
        rich.print(
            f"Data directory already exists at [yellow]{settings.data_path}[/yellow]"
        )


@commands.command()
@click.option("date", "-d", "--date", type=click.DateTime(), default=datetime.now)
@click.option(
    "from_", "-t", "--from", type=str, default=datetime.now().strftime("%H:%M")
)
@click.option("until", "-u", "--until", type=str)
@click.argument("text", type=str)
def add(text: str, date: datetime, from_: str | None = None, until: str | None = None):
    """Add a new event."""
    engine = create_engine(context.settings.sqlite_url)
    from_time = time.fromisoformat(from_)
    duration = (
        datetime.combine(date, time.fromisoformat(until))
        - datetime.combine(date, from_time)
        if until
        else None
    )
    event = Event(date=date, time=from_time, duration=duration, text=text)
    with Session(engine) as session:
        session.add(event)
        session.commit()


@commands.command()
@click.option("date", "-d", "--date", type=click.DateTime(), default=datetime.now)
def list(date: datetime):
    """List events."""
    date = date.date()
    engine = create_engine(context.settings.sqlite_url)
    with Session(engine) as session:
        events = session.exec(select(Event).filter(Event.date == date))
        for e in events:
            rich.print(e)


@commands.command()
@click.argument("text", type=str)
def record(text: str):
    engine = create_engine(context.settings.sqlite_url)
    with Session(engine) as session:
        # Find the current event, whose time is before the current time and whose duration is None
        current_event = session.exec(
            select(Event)
            .filter(
                Event.date == date.today(),
                Event.time <= datetime.now().time(),
                Event.duration == None,  # noqa: E711
            )
            .order_by(Event.time.desc())
        ).first()
        if current_event:
            event_start = datetime.combine(current_event.date, current_event.time)
            event_ends = datetime.now()
            duration = event_ends - event_start
            session.exec(
                update(Event)
                .where(Event.id == current_event.id)
                .values(duration=duration)
            )
            session.commit()
        else:
            rich.print("[red]No previous event found[/red]")
        new_event = Event(date=date.today(), time=datetime.now().time(), text=text)
        session.add(new_event)
        session.commit()
