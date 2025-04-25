from datetime import datetime

import click
import pandas as pd
import rich
from aww import context


@click.group(name="coverage")
def commands():
    pass


@commands.command()
@click.option("bucket", "-b")
@click.option(
    "date_start",
    "--date-start",
    "-s",
    type=click.DateTime(),
    default="1970-01-01",
)
@click.option(
    "date_end",
    "--date-end",
    "-e",
    type=click.DateTime(),
    default="2100-01-01",
)
@click.option("verbose", "-v", is_flag=True)
@click.option("freq", "--freq", "-f", type=str, default="D")
def events(
    bucket: str,
    date_start: datetime,
    date_end: datetime,
    freq: str,
    verbose: bool = False,
):
    """Estimate coverage of training data (feature and labels)."""
    journal = context.journal.subrange(date_start, date_end)
    dates = list(journal.keys())

    if not dates:
        rich.print("[red]No data available.[/red]")
        return

    min_date, max_date = dates[0], dates[-1]
    rich.print(f"Obsidian Date Range: {min_date} ... {max_date}")

    # Create the target PeriodIndex
    td_range = pd.period_range(min_date, max_date, freq=freq)
    rich.print(f"Target Period Range ({freq=}):")
    if verbose:
        rich.print(td_range)
    rich.print(f"Total periods in target range: {len(td_range)}")

    # Get the events DataFrame
    events = journal.event_table().to_pandas()
    if events.empty:
        rich.print("[yellow]No events found in the journal for this range.[/yellow]")
        rich.print("Periods with data: 0")
        return

    # --- Data Preparation ---
    # Ensure correct dtypes and handle potential errors
    events["time"] = pd.to_datetime(events["time"], errors="coerce")
    events["duration"] = pd.to_timedelta(
        events["duration"], errors="coerce"
    )  # Coerce errors to NaT
    events.dropna(
        subset=["time"], inplace=True
    )  # Drop rows where time couldn't be parsed

    # Use 'time' for the index AFTER conversion
    events.set_index("time", inplace=True)
    events.sort_index(
        inplace=True
    )  # Sorting can sometimes help, though not strictly necessary here

    if verbose:
        rich.print("\nEvents DataFrame sample (after type conversion):")
        rich.print(events.head())  # Print head for brevity

    # --- Calculation for Overlapping Periods ---
    all_event_periods = set()

    for timestamp, event_row in events.iterrows():
        try:
            start_period = timestamp.to_period(freq)

            duration = event_row["duration"]
            # Check if duration is valid (not NaT) and positive
            if pd.notna(duration) and duration > pd.Timedelta(0):
                end_time = timestamp + duration
                # Ensure end_time doesn't cause overflow if it's too far in the future
                # pd.Period constructor might raise OutOfBoundsDatetime for very large dates
                try:
                    # Calculate end period, handling potential NaT from overflow
                    end_period_timestamp = pd.Timestamp(end_time).to_period(freq)
                    # Generate periods only if end is after start
                    if end_period_timestamp >= start_period:
                        # Generate periods between start and end (inclusive)
                        spanned_periods = pd.period_range(
                            start=start_period, end=end_period_timestamp, freq=freq
                        )
                        all_event_periods.update(spanned_periods)
                    else:  # Duration was positive but didn't cross a period boundary
                        all_event_periods.add(start_period)
                except (pd.errors.OutOfBoundsDatetime, ValueError):
                    # If end time is out of bounds for Period, just add start period
                    all_event_periods.add(start_period)
                    # Optionally log a warning here
                    # rich.print(f"[yellow]Warning: Event at {timestamp} has duration {duration} resulting in an out-of-bounds end date. Only start period considered.[/yellow]")
            else:
                # No valid duration, just add the start period
                all_event_periods.add(start_period)
        except (pd.errors.OutOfBoundsDatetime, ValueError):
            # If start timestamp itself is out of bounds for Period
            # rich.print(f"[yellow]Warning: Event timestamp {timestamp} is out of bounds for Period frequency {freq}. Skipping.[/yellow]")
            continue  # Skip this event

    # Convert the set of periods to a PeriodIndex for intersection
    # Filter the collected periods to be within reasonable bounds if necessary,
    # although intersection with td_range handles this.
    if not all_event_periods:
        unique_event_periods_index = pd.PeriodIndex([], freq=freq)
    else:
        # Create PeriodIndex from the set
        unique_event_periods_index = pd.PeriodIndex(
            list(all_event_periods), freq=freq
        ).sort_values()

    # rich.print("\nUnique periods covered by events (including duration spans):") # Optional debug print
    # rich.print(unique_event_periods_index)

    # --- Find Intersection and Count ---
    # Intersect with the target date range
    periods_with_data = td_range.intersection(unique_event_periods_index)
    if verbose:
        rich.print(
            "\nPeriods in target range that have data (considering duration):"
        )  # Optional debug print
        rich.print(periods_with_data)

    count_periods_with_data = len(periods_with_data)
    # --- End Calculation ---

    rich.print(
        f"\n[green]Number of periods ({freq=}) with data (considering duration): {count_periods_with_data}[/green]"
    )

    # Optional: Calculate coverage percentage
    if len(td_range) > 0:
        coverage_percentage = (count_periods_with_data / len(td_range)) * 100
        rich.print(f"Label Coverage: {coverage_percentage:.2f}%")
    else:
        rich.print("Label Coverage: N/A (target range is empty)")
