# /home/rlupi/src/augmented-awareness/python/aww/commands/coverage.py
from datetime import datetime
from typing import Tuple

import click
import pandas as pd
import pyarrow as pa  # Import pyarrow
import rich
from aww import context
from aww.observe.activitywatch import (  # Import ActivityWatch
    ActivityWatch,
)


# --- Helper Function for Coverage Calculation ---
def calculate_period_coverage(
    df: pd.DataFrame,
    td_range: pd.PeriodIndex,
    freq: str,
    time_col: str = "time",  # Allow specifying the time column name
    duration_col: str = "duration",  # Allow specifying the duration column name
    verbose: bool = False,
) -> Tuple[int, float, pd.PeriodIndex]:
    """
    Calculates the number and percentage of periods covered by events in a DataFrame.

    Args:
        df: DataFrame containing event data. Must have time and duration columns.
        td_range: The target PeriodIndex range.
        freq: The frequency string for periods (e.g., 'D', 'H').
        time_col: Name of the column containing timestamps.
        duration_col: Name of the column containing durations.
        verbose: If True, print debug information.

    Returns:
        A tuple containing:
        - count_periods_with_data (int): Number of periods in td_range with data.
        - coverage_percentage (float): Percentage of periods covered.
        - periods_with_data (pd.PeriodIndex): The actual periods covered.
    """
    if df.empty:
        return 0, 0.0, pd.PeriodIndex([], freq=freq)

    # --- Data Preparation ---
    # Ensure correct dtypes and handle potential errors
    # Use .get() for duration in case it's missing
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    if duration_col in df.columns:
        df[duration_col] = pd.to_timedelta(df[duration_col], errors="coerce")
    else:
        # If duration column doesn't exist, create it with NaT
        df[duration_col] = pd.NaT

    df.dropna(
        subset=[time_col], inplace=True
    )  # Drop rows where time couldn't be parsed

    # Use the specified time column for the index AFTER conversion
    # Make a copy to avoid SettingWithCopyWarning if df is a slice
    df = df.copy()
    if not isinstance(df.index, pd.DatetimeIndex) or df.index.name != time_col:
        # Check if time_col is already the index
        if time_col in df.columns:
            df.set_index(time_col, inplace=True)
        else:
            # If time_col was already the index and got converted
            df.index.name = time_col  # Just ensure the name is set

    df.sort_index(inplace=True)

    if verbose:
        rich.print(f"\nDataFrame sample for {time_col} (after type conversion):")
        rich.print(df.head())

    # --- Calculation for Overlapping Periods ---
    all_event_periods = set()

    for timestamp, event_row in df.iterrows():
        try:
            start_period = timestamp.to_period(freq)

            duration = event_row.get(duration_col, pd.NaT)  # Use .get() for safety
            # Check if duration is valid (not NaT) and positive
            if pd.notna(duration) and duration > pd.Timedelta(0):
                end_time = timestamp + duration
                try:
                    end_period_timestamp = pd.Timestamp(end_time).to_period(freq)
                    if end_period_timestamp >= start_period:
                        spanned_periods = pd.period_range(
                            start=start_period, end=end_period_timestamp, freq=freq
                        )
                        all_event_periods.update(spanned_periods)
                    else:
                        all_event_periods.add(start_period)
                except (pd.errors.OutOfBoundsDatetime, ValueError):
                    all_event_periods.add(start_period)
            else:
                all_event_periods.add(start_period)
        except (pd.errors.OutOfBoundsDatetime, ValueError):
            continue  # Skip event if start time is out of bounds

    if not all_event_periods:
        unique_event_periods_index = pd.PeriodIndex([], freq=freq)
    else:
        unique_event_periods_index = pd.PeriodIndex(
            list(all_event_periods), freq=freq
        ).sort_values()

    # --- Find Intersection and Count ---
    periods_with_data = td_range.intersection(unique_event_periods_index)
    count_periods_with_data = len(periods_with_data)

    coverage_percentage = 0.0
    if len(td_range) > 0:
        coverage_percentage = (count_periods_with_data / len(td_range)) * 100

    if verbose:
        rich.print(f"\nPeriods in target range covered by {time_col}:")
        rich.print(periods_with_data)

    return count_periods_with_data, coverage_percentage, periods_with_data


@click.group(name="coverage")
def commands():
    pass


@commands.command()
# Remove bucket option as we check multiple sources now
# @click.option("bucket", "-b")
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
    # bucket: str, # Removed
    date_start: datetime,
    date_end: datetime,
    freq: str,
    verbose: bool = False,
):
    """Estimate coverage of label (journal) and feature (ActivityWatch) data."""
    # --- Date Range Setup ---
    # Use journal dates primarily to define the range, but allow overriding?
    # For now, stick to journal defining the absolute min/max
    journal = context.journal.subrange(date_start, date_end)
    dates = list(journal.keys())

    if not dates:
        # If no journal data, maybe still allow checking AW data?
        # For now, require journal data to define the range.
        rich.print("[red]No Journal data available for the specified range.[/red]")
        rich.print("Cannot determine target period range without journal data.")
        return

    min_date, max_date = dates[0], dates[-1]
    # Ensure start/end from options are respected if they narrow the journal range
    min_date = max(min_date, date_start.date()) if date_start else min_date
    max_date = min(max_date, date_end.date()) if date_end else max_date

    # Convert date_start/end to datetime for AW client
    # Use min/max derived from data/options for consistency
    start_dt = datetime.combine(min_date, datetime.min.time())
    end_dt = datetime.combine(max_date, datetime.max.time())

    rich.print(f"Effective Date Range: {min_date} ... {max_date}")

    # Create the target PeriodIndex
    td_range = pd.period_range(min_date, max_date, freq=freq)
    rich.print(f"Target Period Range ({freq=}):")
    if verbose:
        rich.print(td_range)
    rich.print(f"Total periods in target range: {len(td_range)}")
    if len(td_range) == 0:
        rich.print(
            "[yellow]Target period range is empty. No coverage to calculate.[/yellow]"
        )
        return

    # --- Label Coverage (Journal) ---
    rich.print("\n--- Label Data (Journal) ---")
    journal_events = journal.event_table().to_pandas()
    label_count, label_perc, _ = calculate_period_coverage(
        journal_events,
        td_range,
        freq,
        time_col="time",
        duration_col="duration",
        verbose=verbose,
    )
    rich.print(f"Periods with data: [green]{label_count}[/green] ({label_perc:.2f}%)")

    # --- Feature Coverage (ActivityWatch) ---
    rich.print("\n--- Feature Data (ActivityWatch) ---")
    try:
        aw = ActivityWatch()  # Initialize ActivityWatch client
    except Exception as e:
        rich.print(f"[red]Error initializing ActivityWatch client: {e}[/red]")
        rich.print("Skipping feature coverage calculation.")
        return

    feature_sources = {
        "AFK": aw.get_afk,
        "Window": aw.get_currentwindow,
        "Web": aw.get_web_history,
    }

    for name, fetch_func in feature_sources.items():
        rich.print(f"\n[bold]{name} Data:[/bold]")
        try:
            # Fetch data as PyArrow table
            arrow_table = fetch_func(start=start_dt, end=end_dt)
            # Convert to Pandas DataFrame
            feature_df = arrow_table.to_pandas()

            if feature_df.empty:
                rich.print("[yellow]No data found for this period.[/yellow]")
                rich.print("Periods with data: [yellow]0[/yellow] (0.00%)")
                continue

            # ActivityWatch data uses 'timestamp' and 'duration'
            feature_count, feature_perc, _ = calculate_period_coverage(
                feature_df,
                td_range,
                freq,
                time_col="timestamp",  # AW uses 'timestamp'
                duration_col="duration",
                verbose=verbose,
            )
            rich.print(
                f"Periods with data: [green]{feature_count}[/green] ({feature_perc:.2f}%)"
            )

        except StopIteration:
            # This happens if get_buckets_by_type finds no matching bucket
            rich.print(
                f"[yellow]Could not find required ActivityWatch bucket for {name}.[/yellow]"
            )
            rich.print("Periods with data: [yellow]N/A[/yellow]")
        except pa.lib.ArrowIOError as e:
            rich.print(f"[red]Arrow IO Error fetching {name} data: {e}[/red]")
            rich.print("Periods with data: [red]Error[/red]")
        except Exception as e:
            # Catch other potential errors during fetch or processing
            rich.print(f"[red]Error processing {name} data: {e}[/red]")
            import traceback

            if verbose:
                rich.print(traceback.format_exc())
            rich.print("Periods with data: [red]Error[/red]")
