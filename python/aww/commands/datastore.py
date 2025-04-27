import subprocess
import tempfile
from datetime import datetime, time, date
import sys
import os

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


@commands.command()
@click.argument("dt", type=click.DateTime(), default=datetime.now())
def edit(dt: datetime):
    """Edit events for a given date."""
    if "EDITOR" not in os.environ:
        rich.print("[red]EDITOR environment variable not set[/red]")
        sys.exit(1)
    engine = create_engine(context.settings.sqlite_url)
    with Session(engine) as session:
        events = session.exec(select(Event).filter(Event.date == dt.date())).all()
    # 1) Write events to a temporary file
    f = tempfile.NamedTemporaryFile(mode="w", delete=False)
    for e in events:
        f.write(f"{e.as_string()}\n")  # "HH:MM text" or "HH:MM-HH:MM text"
    f.flush()
    # 2) Run the user selected os.environ['EDITOR'] to edit the temporary file
    subprocess.run([os.environ["EDITOR"], f.name])
    # 3) Parse events from the temporary file, if it has changed, and update the database
    with open(f.name, "r") as fd:
        new_events = []
        for line in fd:
            line = line.strip()
            if not line:
                continue
            try:
                new_event = Event.from_string(line, dt)
                new_events.append(new_event)
            except ValueError as e:
                rich.print(f"[red]Error parsing line: {line}[/red]")
                rich.print(f"[red]Error: {e}[/red]")
                sys.exit(1)
    if len(new_events) != len(events):
        rich.print(
            f"[yellow]Number of events changed from {len(events)} to {len(new_events)}[/yellow]"
        )
    else:
        for i, e in enumerate(events):
            if e.as_string() != new_events[i].as_string():
                rich.print(
                    f"[yellow]Event changed from {e.as_string()} to {new_events[i].as_string()}[/yellow]"
                )
                break
        else:
            rich.print("[green]No changes detected[/green]")
            os.unlink(f.name)
            return
    with Session(engine) as session:
        for e in events:
            session.delete(e)
        for e in new_events:
            session.add(e)
        session.commit()
    os.unlink(f.name)
