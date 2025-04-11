import pyarrow as pa


def consolidate_rolling_window(
    data: pa.Table, group_by_columns: list[str] | None = None
) -> pa.Table:
    """Consolidates a table of timeseries data into a table of expanding window data.

    The timeseries data should contain a column named 'duration' which is a timedelta64[ns] type.
    The table should also contain a column named 'timestamp' which is a datetime64[ns] type.

    Successive rows with the same group_by_columns will be consolidated into a single row
    with cumulative duration. New rows are created when group_by_columns change.

    Args:
        data (pa.Table): The table of timeseries data to consolidate.
        group_by_columns (list[str], optional): The columns to group by. Defaults to None.
    Returns:
        pa.Table: The consolidated table of expanding window data.
    """
    # Validate required columns exist
    required_columns = {"timestamp", "duration"}
    if not required_columns.issubset(data.column_names):
        raise ValueError(f"Input table must contain columns: {required_columns}")

    # Convert to pandas DataFrame for time-based operations
    df = data.to_pandas()

    # Determine grouping columns
    if group_by_columns is None:
        group_by_columns = [col for col in df.columns if col not in required_columns]

    # Sort by timestamp to ensure chronological order
    df = df.sort_values("timestamp")

    # Identify change points in group_by_columns
    if group_by_columns:
        df["group_change"] = (df[group_by_columns] != df[group_by_columns].shift()).any(
            axis=1
        )
        df["group_id"] = df["group_change"].cumsum()
    else:
        df["group_id"] = 0

    # Group by the change points and sum durations
    grouped = df.groupby("group_id", as_index=False)
    consolidated = grouped.agg(
        {
            "duration": "sum",
            "timestamp": "first",  # Keep first timestamp in group
            **{
                col: "first" for col in group_by_columns
            },  # Keep first value of each group column
        }
    )

    # Drop temporary columns
    consolidated = consolidated.drop(columns=["group_id"])
    if "group_change" in consolidated.columns:
        consolidated = consolidated.drop(columns=["group_change"])

    # Convert back to pyarrow Table
    return pa.Table.from_pandas(consolidated)
