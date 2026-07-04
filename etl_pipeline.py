import os
import sys
import logging
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import config

# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(config.LOG_FILE_PATH), exist_ok=True)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_FILE_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)


def extract(file_path):
    """
    Extracts data from the specified CSV file.
    """
    logging.info("--- Extraction Phase Started ---")
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source CSV file not found at: {file_path}")

        logging.info(f"Reading data from {file_path}")
        df = pd.read_csv(file_path)
        logging.info(f"Successfully extracted {len(df)} records.")
        return df
    except FileNotFoundError as fnf_error:
        logging.error(f"Extraction failed: {fnf_error}")
        raise
    except Exception as e:
        logging.error(f"Extraction failed due to an unexpected error: {e}")
        raise


def transform(df):
    """
    Transforms the extracted DataFrame based on the project requirements:
    1. Remove duplicate records.
    2. Handle missing values.
    3. Convert customer names to uppercase.
    4. Create a new column Total = Price * Quantity.
    """
    logging.info("--- Transformation Phase Started ---")
    try:
        # Create a copy of the dataframe to avoid setting with copy warnings
        df_cleaned = df.copy()

        # 1. Remove duplicate records
        initial_count = len(df_cleaned)
        df_cleaned.drop_duplicates(inplace=True)
        final_count = len(df_cleaned)
        duplicates_removed = initial_count - final_count
        logging.info(
            f"Removed {duplicates_removed} duplicate records. Row count reduced from {initial_count} to {final_count}."
        )

        # 2. Handle missing values
        # Customer_Name: fill missing values with "UNKNOWN"
        missing_names = df_cleaned["Customer_Name"].isnull().sum()
        df_cleaned["Customer_Name"] = df_cleaned["Customer_Name"].fillna("UNKNOWN")
        if missing_names > 0:
            logging.info(
                f"Handled {missing_names} missing customer names (replaced with 'UNKNOWN')."
            )

        # Price: fill missing values with 0.0, convert to float
        missing_prices = df_cleaned["Price"].isnull().sum()
        df_cleaned["Price"] = pd.to_numeric(
            df_cleaned["Price"], errors="coerce"
        ).fillna(0.0)
        if missing_prices > 0:
            logging.info(
                f"Handled {missing_prices} missing prices (replaced with 0.0)."
            )

        # Quantity: fill missing values with 0, convert to integer
        missing_quantities = df_cleaned["Quantity"].isnull().sum()
        df_cleaned["Quantity"] = (
            pd.to_numeric(df_cleaned["Quantity"], errors="coerce").fillna(0).astype(int)
        )
        if missing_quantities > 0:
            logging.info(
                f"Handled {missing_quantities} missing quantities (replaced with 0)."
            )

        # 3. Convert customer names to uppercase
        df_cleaned["Customer_Name"] = (
            df_cleaned["Customer_Name"].astype(str).str.upper()
        )
        logging.info("Converted customer names to uppercase.")

        # 4. Create a new column Total = Price * Quantity
        df_cleaned["Total"] = df_cleaned["Price"] * df_cleaned["Quantity"]
        logging.info("Calculated 'Total' column as Price * Quantity.")

        logging.info("Transformation phase completed successfully.")
        return df_cleaned
    except Exception as e:
        logging.error(f"Transformation failed: {e}")
        raise


def load(df, db_url, db_name, table_name):
    """
    Loads the transformed DataFrame into the MySQL database.
    Creates the database if it doesn't exist, then loads the table.
    """
    logging.info("--- Loading Phase Started ---")
    try:
        # Step 1: Connect to MySQL server without specifying database to ensure database exists
        server_url = db_url.rsplit("/", 1)[
            0
        ]  # Extracts mysql+pymysql://user:pass@host:port
        logging.info(f"Connecting to MySQL server to check/create database: {db_name}")
        server_engine = create_engine(server_url)

        with server_engine.connect() as conn:
            # We must use execution_options(isolation_level="AUTOCOMMIT") to run CREATE DATABASE
            conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                text(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            )
        logging.info(f"Database '{db_name}' verified/created successfully.")

        # Step 2: Connect to the specific database and load the table
        logging.info(f"Loading transformed data to table '{table_name}'")
        db_engine = create_engine(db_url)

        # Load the DataFrame to SQL (replace table if it exists)
        df.to_sql(name=table_name, con=db_engine, if_exists="replace", index=False)
        logging.info(
            f"Successfully loaded {len(df)} records into '{db_name}.{table_name}' table."
        )

    except SQLAlchemyError as sa_error:
        logging.error(f"Database loading failed (SQLAlchemy error): {sa_error}")
        raise
    except Exception as e:
        logging.error(f"Loading failed due to an unexpected error: {e}")
        raise


def run_etl():
    """
    Orchestrates the entire ETL pipeline.
    """
    logging.info("=========================================")
    logging.info("ETL Pipeline Execution Initiated")
    logging.info("=========================================")
    try:
        # Step 1: Extract
        raw_data = extract(config.CSV_FILE_PATH)

        # Step 2: Transform
        transformed_data = transform(raw_data)

        # Step 3: Load
        load(
            df=transformed_data,
            db_url=config.DB_CONNECTION_URL,
            db_name=config.DB_NAME,
            table_name=config.DB_TABLE,
        )

        logging.info("=========================================")
        logging.info("ETL Pipeline Executed Successfully!")
        logging.info("=========================================")
    except Exception as e:
        logging.error("=========================================")
        logging.error(f"ETL Pipeline execution failed: {e}")
        logging.error("=========================================")
        sys.exit(1)


if __name__ == "__main__":
    run_etl()
