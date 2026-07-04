import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError
import etl_pipeline


# Sample test data matching raw sales.csv format
@pytest.fixture
def sample_raw_data():
    return pd.DataFrame(
        {
            "Transaction_ID": [1, 2, 2, 3, 4, 5],
            "Date": [
                "2026-07-01",
                "2026-07-02",
                "2026-07-02",
                "2026-07-03",
                "2026-07-04",
                "2026-07-05",
            ],
            "Customer_Name": ["Alice", "Bob", "Bob", None, "Charlie", "David"],
            "Product": [
                "Laptop",
                "Mouse",
                "Mouse",
                "Keyboard",
                "Monitor",
                "Headphones",
            ],
            "Price": ["1200.00", "25.50", "25.50", "invalid_price", None, "50.00"],
            "Quantity": ["1", "2", "2", "3", "2", None],
        }
    )


def test_extract_success(tmp_path, sample_raw_data):
    # Create a temporary CSV file
    csv_file = tmp_path / "test_sales.csv"
    sample_raw_data.to_csv(csv_file, index=False)

    # Run extract
    df = etl_pipeline.extract(str(csv_file))

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 6
    assert list(df.columns) == [
        "Transaction_ID",
        "Date",
        "Customer_Name",
        "Product",
        "Price",
        "Quantity",
    ]


def test_extract_file_not_found():
    with pytest.raises(FileNotFoundError):
        etl_pipeline.extract("non_existent_file.csv")


def test_transform(sample_raw_data):
    # Run transform
    df_transformed = etl_pipeline.transform(sample_raw_data)

    # 1. Deduplication (6 rows -> 5 rows, because row index 2 is duplicate of row index 1)
    assert len(df_transformed) == 5

    # Reset index to test specific rows easily
    df_transformed = df_transformed.reset_index(drop=True)

    # 2. Missing customer names filled with "UNKNOWN"
    assert df_transformed.loc[2, "Customer_Name"] == "UNKNOWN"  # originally row index 3

    # 3. Customer name casing should be uppercase
    assert df_transformed.loc[0, "Customer_Name"] == "ALICE"
    assert df_transformed.loc[1, "Customer_Name"] == "BOB"
    assert df_transformed.loc[3, "Customer_Name"] == "CHARLIE"

    # 4. Price handling (invalid_price -> 0.0, None -> 0.0)
    assert df_transformed.loc[2, "Price"] == 0.0  # 'invalid_price'
    assert df_transformed.loc[3, "Price"] == 0.0  # None
    assert df_transformed.loc[0, "Price"] == 1200.00

    # 5. Quantity handling (None -> 0, cast to int)
    assert df_transformed.loc[4, "Quantity"] == 0  # None
    assert isinstance(
        df_transformed.loc[4, "Quantity"], (int, pytest.importorskip("numpy").integer)
    )
    assert df_transformed.loc[1, "Quantity"] == 2

    # 6. Total = Price * Quantity
    assert df_transformed.loc[0, "Total"] == 1200.00 * 1
    assert df_transformed.loc[1, "Total"] == 25.50 * 2
    assert df_transformed.loc[2, "Total"] == 0.0
    assert df_transformed.loc[4, "Total"] == 50.00 * 0


@patch("etl_pipeline.create_engine")
def test_load_success(mock_create_engine, sample_raw_data):
    # Setup mocks
    mock_server_engine = MagicMock()
    mock_db_engine = MagicMock()

    # Side effect for create_engine:
    # First call is for server, second is for specific db
    mock_create_engine.side_effect = [mock_server_engine, mock_db_engine]

    mock_conn = MagicMock()
    mock_server_engine.connect.return_value.__enter__.return_value = mock_conn
    mock_conn.execution_options.return_value = mock_conn

    # Create test dataframe (already transformed)
    df_transformed = etl_pipeline.transform(sample_raw_data)

    # Run load
    etl_pipeline.load(
        df=df_transformed,
        db_url="mysql+pymysql://user:pass@localhost:3306/test_db",
        db_name="test_db",
        table_name="test_table",
    )

    # Verify server engine creation (connection URL without DB name)
    mock_create_engine.assert_any_call("mysql+pymysql://user:pass@localhost:3306")

    # Verify CREATE DATABASE statement execution
    mock_conn.execution_options.assert_called_with(isolation_level="AUTOCOMMIT")
    mock_conn.execute.assert_called()

    # Verify db engine creation
    mock_create_engine.assert_any_call(
        "mysql+pymysql://user:pass@localhost:3306/test_db"
    )


@patch("etl_pipeline.create_engine")
def test_load_db_failure(mock_create_engine, sample_raw_data):
    # Make create_engine raise an error
    mock_create_engine.side_effect = SQLAlchemyError("Connection failed")

    df_transformed = etl_pipeline.transform(sample_raw_data)

    with pytest.raises(SQLAlchemyError):
        etl_pipeline.load(
            df=df_transformed,
            db_url="mysql+pymysql://user:pass@localhost:3306/test_db",
            db_name="test_db",
            table_name="test_table",
        )
