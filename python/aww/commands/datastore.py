import math
import subprocess
import tempfile
from collections import defaultdict
from datetime import datetime, time, date, timedelta
import sys
import os

import click
import rich
import rich.prompt
from sqlmodel import create_engine, SQLModel, Session, select, update, delete

from aww import context

import aww.datastore.models  # noqa: F401

from aww.datastore.models import Event

from aww.commands.schedule import generate_sparkline
from aww.orient.schedule import histogram_bins


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


@commands.command(name="list")
@click.option("date", "-d", "--date", type=click.DateTime(), default=datetime.now)
def list_events(date: datetime):
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
                    f"[yellow]At least, one event changed from {e.as_string()} to {new_events[i].as_string()}[/yellow]"
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


@commands.command()
@click.option(
    "start_date", "-s", "--start", type=click.DateTime(), default=datetime(1970, 1, 1)
)
@click.option(
    "end_date", "-e", "--end", type=click.DateTime(), default=datetime(2100, 1, 1)
)
def import_events(start_date: datetime, end_date: datetime):
    """Copy over events from Obsidian vault."""
    rich.print(f"Importing events between {start_date:%H:%M} and {end_date:%H:%M}")
    dates = context.journal.subrange(start_date.date(), end_date.date())
    engine = create_engine(context.settings.sqlite_url)
    with Session(engine) as session:
        for dt, page in dates.items():
            events = list(page.events())
            if not events:
                continue
            rich.print(dt)
            session.exec(delete(Event).where(Event.date == dt))
            for ev in events:
                rich.print("  ", ev)
                event = Event(
                    date=ev.time.date(),
                    time=ev.time.time(),
                    duration=ev.duration,
                    text=ev.name,
                )
                session.add(event)
            session.commit()


@commands.command()
@click.option(
    "date_start",
    "--date-start",
    "-s",
    type=click.DateTime(),
    default=(date.today() - timedelta(days=8)).strftime("%Y-%m-%d"),
    help="Start date (YYYY-MM-DD).",
)
@click.option(
    "date_end",
    "--date-end",
    "-e",
    type=click.DateTime(),
    default=(date.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
    help="End date (YYYY-MM-DD).",
)
@click.option(
    "date_opt",  # Renamed to avoid conflict with date type
    "--date",
    "-d",
    help="Specify a single date (overrides date_start and date_end, YYYY-MM-DD).",
    type=click.DateTime(),
    default=None,
)
@click.option(
    "today_flag", "-t", "--today", is_flag=True, help="Set dates to today."
)  # Renamed to avoid conflict
@click.option(
    "histogram_resolution_minutes",
    "--resolution",
    type=int,
    default=30,
    show_default=True,
    help="Histogram resolution in minutes.",
)
def busy(
    date_start: datetime,
    date_end: datetime,
    date_opt: datetime | None,
    today_flag: bool,
    histogram_resolution_minutes: int,
):
    """Reports the total time by tag using events from the datastore."""
    start_d: date = date_start.date()
    end_d: date = date_end.date()
    if date_opt:
        start_d = date_opt.date()
        end_d = date_opt.date()
    elif today_flag:
        start_d = date.today()
        end_d = date.today()

    rich.print(f"Analyzing datastore events from {start_d} to {end_d}")

    engine = create_engine(context.settings.sqlite_url)
    # Use defaultdict for easier initialization
    totals = defaultdict(lambda: timedelta(seconds=0))
    histograms = defaultdict(list)
    histogram_resolution = timedelta(minutes=histogram_resolution_minutes)

    # Ensure resolution is positive
    if histogram_resolution.total_seconds() <= 0:
        rich.print("[red]Histogram resolution must be positive.[/red]")
        sys.exit(1)

    n_buckets = int(
        math.ceil(
            timedelta(days=1).total_seconds() / histogram_resolution.total_seconds()
        )
    )

    with Session(engine) as session:
        query = select(Event).filter(Event.date >= start_d, Event.date <= end_d)
        events = session.exec(query).all()

    if not events:
        rich.print(
            "[yellow]No events found in the datastore for the specified date range.[/yellow]"
        )
        return

    for event in events:
        # Extract tags using the imported regex
        # Default duration to zero if None for calculations
        duration = event.duration or timedelta(seconds=0)

        for tag in event.tags:
            # Ensure histogram list is initialized with the correct number of zeros
            if tag not in histograms:
                histograms[tag] = [0] * n_buckets

            totals[tag] += duration

            # Add to histogram only if event has a time
            if event.time:
                # histogram_bins needs a non-zero duration.
                # If original duration is None or zero, use the resolution interval.
                bin_duration = event.duration
                if not bin_duration or bin_duration.total_seconds() <= 0:
                    bin_duration = histogram_resolution

                try:
                    for n in histogram_bins(event.time, bin_duration, n_buckets):
                        # Check bounds just in case, though histogram_bins should be correct
                        if 0 <= n < n_buckets:
                            histograms[tag][n] += 1
                        else:
                            rich.print(
                                f"[yellow]Warning: histogram bin index {n} out of bounds (0-{n_buckets - 1}) for event '{event.text}'[/yellow]"
                            )
                except Exception as e:
                    # Catch potential errors during histogram calculation for a specific event
                    rich.print(
                        f"[red]Error calculating histogram for event '{event.text}' ({event.time}, {bin_duration}): {e}[/red]"
                    )

    # Prepare data for table, sorting by total duration descending
    sorted_tags = sorted(totals.items(), key=lambda item: item[1], reverse=True)

    if not sorted_tags:
        rich.print(
            "[yellow]No tags found in the events for the specified date range.[/yellow]"
        )
        return

    # Create and print the rich table
    t = rich.table.Table(title=f"Time Spent by Tag (Datastore: {start_d} to {end_d})")
    t.add_column("Tag", justify="left", style="cyan", no_wrap=True)
    t.add_column("Total Duration", justify="right", style="magenta")
    t.add_column(
        f"Activity Histogram ({histogram_resolution_minutes}min bins)",
        justify="left",
        style="green",
        no_wrap=True,
    )

    for tag, total_duration in sorted_tags:
        # Get histogram data, default to zeros if tag somehow only existed in events without time
        histogram_data = histograms.get(tag, [0] * n_buckets)
        t.add_row(
            f"#{tag}",  # Add '#' prefix back for display
            str(total_duration),
            generate_sparkline(histogram_data),
        )

    rich.print(t)
