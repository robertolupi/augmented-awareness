import pytest
import pyarrow as pa
import pandas as pd
import numpy as np
import datetime

from aww.orient.timeseries import consolidate_timestamp_duration

# --- Fixtures for Test Data ---


@pytest.fixture
def sample_data_dict():
    """Provides a sample dictionary for creating test tables."""
    return {
        "timestamp": [
            datetime.datetime(2023, 1, 1, 10, 0, 0),
            datetime.datetime(2023, 1, 1, 10, 0, 5),
            datetime.datetime(2023, 1, 1, 10, 0, 15),  # Group change
            datetime.datetime(2023, 1, 1, 10, 0, 20),
            datetime.datetime(2023, 1, 1, 10, 0, 30),  # Group change
            datetime.datetime(2023, 1, 1, 10, 0, 35),
            datetime.datetime(2023, 1, 1, 10, 0, 45),  # Group change (back to A)
            datetime.datetime(2023, 1, 1, 10, 0, 50),
        ],
        "duration": [
            np.timedelta64(5, "s"),
            np.timedelta64(10, "s"),
            np.timedelta64(5, "s"),
            np.timedelta64(10, "s"),
            np.timedelta64(5, "s"),
            np.timedelta64(10, "s"),
            np.timedelta64(5, "s"),
            np.timedelta64(10, "s"),
        ],
        "label": ["A", "A", "B", "B", "C", "C", "A", "A"],
        "value": [1, 1, 2, 2, 3, 3, 1, 1],  # Corresponds to label
    }


@pytest.fixture
def sample_pa_table(sample_data_dict):
    """Provides a sample pyarrow Table."""
    # Ensure correct types for pyarrow
    data = sample_data_dict.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    data["duration"] = pd.to_timedelta(data["duration"])
    df = pd.DataFrame(data)
    return pa.Table.from_pandas(df)


@pytest.fixture
def sample_pa_table_unsorted(sample_data_dict):
    """Provides an unsorted sample pyarrow Table."""
    data = sample_data_dict.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"])
    data["duration"] = pd.to_timedelta(data["duration"])
    df = pd.DataFrame(data)
    # Shuffle the dataframe
    df = df.sample(frac=1).reset_index(drop=True)
    return pa.Table.from_pandas(df)


@pytest.fixture
def empty_pa_table():
    """Provides an empty pyarrow Table with the correct schema."""
    schema = pa.schema(
        [
            pa.field("timestamp", pa.timestamp("ns")),
            pa.field("duration", pa.duration("ns")),
            pa.field("label", pa.string()),
            pa.field("value", pa.int64()),
        ]
    )
    return pa.Table.from_pylist([], schema=schema)


@pytest.fixture
def single_row_pa_table():
    """Provides a pyarrow Table with a single row."""
    data = {
        "timestamp": [datetime.datetime(2023, 1, 1, 10, 0, 0)],
        "duration": [np.timedelta64(5, "s")],
        "label": ["A"],
        "value": [1],
    }
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["duration"] = pd.to_timedelta(df["duration"])
    return pa.Table.from_pandas(df)


# --- Test Cases ---


def test_consolidate_with_grouping(sample_pa_table):
    """Tests consolidation with specified group_by_columns."""
    group_cols = ["label", "value"]
    result_table = consolidate_timestamp_duration(
        sample_pa_table, group_by_columns=group_cols
    )

    expected_data = {
        "duration": [
            np.timedelta64(15, "s"),  # A, 1
            np.timedelta64(15, "s"),  # B, 2
            np.timedelta64(15, "s"),  # C, 3
            np.timedelta64(15, "s"),  # A, 1 (again)
        ],
        "timestamp": [
            datetime.datetime(2023, 1, 1, 10, 0, 0),
            datetime.datetime(2023, 1, 1, 10, 0, 15),
            datetime.datetime(2023, 1, 1, 10, 0, 30),
            datetime.datetime(2023, 1, 1, 10, 0, 45),
        ],
        "label": ["A", "B", "C", "A"],
        "value": [1, 2, 3, 1],
    }
    expected_df = pd.DataFrame(expected_data)
    # Ensure correct dtypes for comparison
    expected_df["timestamp"] = pd.to_datetime(expected_df["timestamp"])
    expected_df["duration"] = pd.to_timedelta(expected_df["duration"])

    # Sort columns for reliable comparison
    result_df = result_table.to_pandas().sort_index(axis=1)
    expected_df_sorted = expected_df.sort_index(axis=1)

    pd.testing.assert_frame_equal(result_df, expected_df_sorted, check_dtype=True)
    # Alternatively, use pyarrow equals, but requires exact schema match including metadata
    # expected_table = pa.Table.from_pandas(expected_df)
    # assert result_table.equals(expected_table)


def test_consolidate_no_grouping(sample_pa_table):
    """Tests consolidation when group_by_columns is None (uses all non-required cols)."""
    result_table = consolidate_timestamp_duration(sample_pa_table, group_by_columns=None)

    # Expected result is the same as grouping by ['label', 'value'] in this specific sample data
    expected_data = {
        "duration": [
            np.timedelta64(15, "s"),  # A, 1
            np.timedelta64(15, "s"),  # B, 2
            np.timedelta64(15, "s"),  # C, 3
            np.timedelta64(15, "s"),  # A, 1 (again)
        ],
        "timestamp": [
            datetime.datetime(2023, 1, 1, 10, 0, 0),
            datetime.datetime(2023, 1, 1, 10, 0, 15),
            datetime.datetime(2023, 1, 1, 10, 0, 30),
            datetime.datetime(2023, 1, 1, 10, 0, 45),
        ],
        "label": ["A", "B", "C", "A"],
        "value": [1, 2, 3, 1],
    }
    expected_df = pd.DataFrame(expected_data)
    expected_df["timestamp"] = pd.to_datetime(expected_df["timestamp"])
    expected_df["duration"] = pd.to_timedelta(expected_df["duration"])

    result_df = result_table.to_pandas().sort_index(axis=1)
    expected_df_sorted = expected_df.sort_index(axis=1)

    pd.testing.assert_frame_equal(result_df, expected_df_sorted, check_dtype=True)


def test_consolidate_only_required_columns():
    """Tests consolidation when only timestamp and duration exist."""
    data = {
        "timestamp": pd.to_datetime(
            [
                datetime.datetime(2023, 1, 1, 10, 0, 0),
                datetime.datetime(2023, 1, 1, 10, 0, 5),
                datetime.datetime(2023, 1, 1, 10, 0, 15),
            ]
        ),
        "duration": pd.to_timedelta(
            [
                np.timedelta64(5, "s"),
                np.timedelta64(10, "s"),
                np.timedelta64(5, "s"),
            ]
        ),
    }
    input_table = pa.Table.from_pandas(pd.DataFrame(data))
    result_table = consolidate_timestamp_duration(input_table, group_by_columns=None)

    # Without grouping columns, all rows are consolidated into one
    expected_data = {
        "duration": [np.timedelta64(20, "s")],
        "timestamp": [datetime.datetime(2023, 1, 1, 10, 0, 0)],
    }
    expected_df = pd.DataFrame(expected_data)
    expected_df["timestamp"] = pd.to_datetime(expected_df["timestamp"])
    expected_df["duration"] = pd.to_timedelta(expected_df["duration"])

    result_df = result_table.to_pandas().sort_index(axis=1)
    expected_df_sorted = expected_df.sort_index(axis=1)

    pd.testing.assert_frame_equal(result_df, expected_df_sorted, check_dtype=True)


def test_consolidate_unsorted_data(sample_pa_table_unsorted, sample_pa_table):
    """Tests that unsorted input data is correctly sorted and processed."""
    group_cols = ["label", "value"]
    result_table_unsorted = consolidate_timestamp_duration(
        sample_pa_table_unsorted, group_by_columns=group_cols
    )
    result_table_sorted = consolidate_timestamp_duration(
        sample_pa_table, group_by_columns=group_cols
    )  # Use sorted fixture for expected

    # The result should be the same regardless of initial sort order
    assert result_table_unsorted.equals(result_table_sorted)


def test_consolidate_empty_table(empty_pa_table):
    """Tests consolidation with an empty input table."""
    result_table = consolidate_timestamp_duration(
        empty_pa_table, group_by_columns=["label", "value"]
    )

    # Expect an empty table with the same (or derived) schema
    assert result_table.num_rows == 0
    # Check if essential columns exist in the output schema
    assert "timestamp" in result_table.schema.names
    assert "duration" in result_table.schema.names
    assert "label" in result_table.schema.names  # Grouping cols should be preserved
    assert "value" in result_table.schema.names


def test_consolidate_single_row(single_row_pa_table):
    """Tests consolidation with a single row input table."""
    group_cols = ["label", "value"]
    result_table = consolidate_timestamp_duration(
        single_row_pa_table, group_by_columns=group_cols
    )

    # Expect the output to be identical to the input (after potential schema changes from pandas conversion)
    expected_df = single_row_pa_table.to_pandas()
    result_df = result_table.to_pandas()

    # Sort columns for reliable comparison
    result_df = result_df.sort_index(axis=1)
    expected_df = expected_df.sort_index(axis=1)

    pd.testing.assert_frame_equal(result_df, expected_df, check_dtype=True)


def test_missing_timestamp_column(sample_pa_table):
    """Tests that ValueError is raised if 'timestamp' column is missing."""
    table_missing_ts = sample_pa_table.drop_columns(["timestamp"])
    with pytest.raises(
        ValueError, match="Input table must contain columns:.*'timestamp'"
    ):
        consolidate_timestamp_duration(table_missing_ts, group_by_columns=["label"])


def test_missing_duration_column(sample_pa_table):
    """Tests that ValueError is raised if 'duration' column is missing."""
    table_missing_dur = sample_pa_table.drop_columns(["duration"])
    with pytest.raises(
        ValueError, match="Input table must contain columns:.*'duration'"
    ):
        consolidate_timestamp_duration(table_missing_dur, group_by_columns=["label"])
