# Python ETL Pipeline Project

This project implements a fully automated Extract, Transform, and Load (ETL) pipeline using Python. It extracts raw sales data from a CSV file (`sales.csv`), performs various cleaning and formatting transformations using `pandas`, and loads the final clean data into a MySQL database table using `SQLAlchemy` and `PyMySQL`.

---

## Project Structure

```text
etl_pipeline/
├── data/
│   └── sales.csv             # Raw input dataset
├── logs/
│   └── etl.log               # Log file containing run history (auto-created)
├── config.py                 # Application connection & path configurations
├── etl_pipeline.py           # Main ETL script containing execution logic
├── requirements.txt          # Python dependencies
└── README.md                 # Documentation, code walkthroughs, & run guide
```

---

## Dependencies

The project relies on the following standard data engineering libraries:
1. **Pandas**: Used for extraction (reading CSV) and transformations (manipulating dataframes).
2. **SQLAlchemy**: An Object-Relational Mapper (ORM) that provides SQL connection engines for database communication.
3. **PyMySQL**: A pure-Python MySQL client database driver that works seamlessly with SQLAlchemy.
4. **Cryptography**: Required by PyMySQL/SQLAlchemy for modern password encryption during authentication.

---

## Step-by-Step Execution Guide

### 1. Prerequisites
Ensure you have Python 3.8+ installed on your system. You also need a running MySQL database server.

### 2. Database Configuration
By default, the script connects to a database named `etl_db`.
* **If you have a MySQL server running**: Open [config.py](file:///C:/Users/RACHANA%20KULKARNI/.gemini/antigravity/scratch/etl_pipeline/config.py) and update the credentials (`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`) to match your local setup.
* Alternatively, you can set them using environment variables:
  * `ETL_DB_USER`
  * `ETL_DB_PASSWORD`
  * `ETL_DB_HOST`
  * `ETL_DB_PORT`
  * `ETL_DB_NAME`

The script will automatically attempt to connect and create the database `etl_db` if it doesn't already exist.

### 3. Installation
Navigate to the project root directory and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 4. Running the Pipeline
Run the main ETL pipeline script:
```bash
python etl_pipeline.py
```

### 5. Check Output and Logs
* Check the terminal output for real-time progress.
* View [logs/etl.log](file:///C:/Users/RACHANA%20KULKARNI/.gemini/antigravity/scratch/etl_pipeline/logs/etl.log) for the complete audit trail of the run.
* Connect to your MySQL client and inspect the loaded table:
  ```sql
  USE etl_db;
  SELECT * FROM sales_transformed;
  ```

---

## Line-by-Line Code Walkthrough

### 1. `config.py`

| Line(s) | Code | Explanation |
| :--- | :--- | :--- |
| `1` | `import os` | Imports the standard Python library `os` to work with environment variables and filepath generation. |
| `3` | `DB_USER = os.getenv("ETL_DB_USER", "root")` | Retrieves the DB username from environment variables, defaulting to `"root"` if not set. |
| `4` | `DB_PASSWORD = os.getenv("ETL_DB_PASSWORD", "password_here")` | Retrieves the DB password, defaulting to `"password_here"`. Make sure to replace this with your actual MySQL password. |
| `5` | `DB_HOST = os.getenv("ETL_DB_HOST", "localhost")` | Retrieves the database host address, defaulting to `"localhost"`. |
| `6` | `DB_PORT = int(os.getenv("ETL_DB_PORT", "3306"))` | Retrieves the database port (defaults to `3306`) and converts it to an integer. |
| `7` | `DB_NAME = os.getenv("ETL_DB_NAME", "etl_db")` | Retrieves the target database name, defaulting to `"etl_db"`. |
| `8` | `DB_TABLE = "sales_transformed"` | Sets a constant for the MySQL target table name. |
| `11` | `CSV_FILE_PATH = os.path.join("data", "sales.csv")` | Construct the cross-platform file path to the source CSV data file under `data/sales.csv`. |
| `12` | `LOG_FILE_PATH = os.path.join("logs", "etl.log")` | Construct the cross-platform file path to store logs under `logs/etl.log`. |
| `16` | `DB_CONNECTION_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"` | Builds the SQLAlchemy database connection URL using the `mysql+pymysql` dialect. |

---

### 2. `etl_pipeline.py`

#### Imports and Setup (Lines 1–18)
* `import os`, `import sys`: Used for OS operations (like directory creation) and exiting the program on fatal errors.
* `import logging`: Python's built-in module to record pipeline steps and error traces.
* `import pandas as pd`: Imports Pandas under the standard alias `pd` for dataframe manipulation.
* `from sqlalchemy import create_engine, text`: Imports SQLAlchemy tools to instantiate a connection engine and execute raw SQL statements.
* `from sqlalchemy.exc import SQLAlchemyError`: Imports the exception class for catching database-related errors.
* `import config`: Imports configuration variables defined in [config.py](file:///C:/Users/RACHANA%20KULKARNI/.gemini/antigravity/scratch/etl_pipeline/config.py).
* `os.makedirs(os.path.dirname(config.LOG_FILE_PATH), exist_ok=True)`: Creates the parent folder for logs if it doesn't already exist.
* `logging.basicConfig(...)`: Configures logging. It outputs logs to both the file (`logs/etl.log`) and standard output (`sys.stdout`) with a timestamp, log level, and description message.

#### Extraction Phase (Lines 20–38)
```python
def extract(file_path):
```
* Defs the extraction function.
* `if not os.path.exists(file_path)`: Verifies if the source CSV file exists. If not, raises a `FileNotFoundError`.
* `df = pd.read_csv(file_path)`: Reads the CSV file using Pandas and loads it into memory as a DataFrame.
* `logging.info(f"Successfully extracted {len(df)} records.")`: Logs the count of records loaded.
* `except` blocks catch missing files or generic parser errors, logging the error and re-raising the exception to halt pipeline execution.

#### Transformation Phase (Lines 40–86)
```python
def transform(df):
```
* Defs the transformation function.
* `df_cleaned = df.copy()`: Creates a deep copy of the dataframe to prevent modifying the original dataframe and avoid pandas `SettingWithCopy` warnings.
* **Deduplication**:
  * `initial_count = len(df_cleaned)`: Stores original row count.
  * `df_cleaned.drop_duplicates(inplace=True)`: Drops exact duplicate records.
  * `duplicates_removed = initial_count - len(df_cleaned)`: Logs how many duplicate records were found and removed.
* **Handling Missing Values**:
  * `df_cleaned['Customer_Name'].fillna("UNKNOWN")`: Replaces empty customer fields with `"UNKNOWN"`.
  * `pd.to_numeric(df_cleaned['Price'], errors='coerce').fillna(0.0)`: Coerces invalid price entries (such as non-numeric strings) into NaNs, then fills all NaNs with `0.0`.
  * `pd.to_numeric(df_cleaned['Quantity'], errors='coerce').fillna(0).astype(int)`: Coerces invalid quantity entries to NaNs, fills NaNs with `0`, and casts the column to integers.
* **Case Normalization**:
  * `df_cleaned['Customer_Name'].astype(str).str.upper()`: Converts all customer names to uppercase for standardized reporting.
* **Derived Columns**:
  * `df_cleaned['Total'] = df_cleaned['Price'] * df_cleaned['Quantity']`: Calculates the line-item total by multiplying Price and Quantity.

#### Loading Phase (Lines 88–123)
```python
def load(df, db_url, db_name, table_name):
```
* Defs the loading function.
* `server_url = db_url.rsplit('/', 1)[0]`: Strips the database name from the URL string. This is necessary because if the database `etl_db` does not exist yet, trying to connect to it directly will cause an error.
* `server_engine = create_engine(server_url)`: Connects to the root MySQL server.
* `conn.execution_options(isolation_level="AUTOCOMMIT").execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name}"))`: Runs an SQL query to create the database if it doesn't already exist. `AUTOCOMMIT` is required here because CREATE DATABASE queries cannot run inside transactions.
* `db_engine = create_engine(db_url)`: Reconnects directly to the verified database.
* `df.to_sql(name=table_name, con=db_engine, if_exists="replace", index=False)`: Uses Pandas + SQLAlchemy to convert the DataFrame to a database table. `if_exists="replace"` ensures that the table structure is overwritten with fresh data if it already exists, and `index=False` prevents writing the dataframe index as an extra database column.
* `except SQLAlchemyError as sa_error`: Specific database driver exceptions are caught and logged.

#### Orchestrator Function (Lines 125–158)
```python
def run_etl():
```
* Serves as the pipeline controller.
* Executes `extract()`, followed by `transform()`, and then `load()` sequentially.
* If any step fails, logs a fatal error and calls `sys.exit(1)` to return a non-zero exit code to the shell (useful in production orchestrators like Airflow or cron jobs).
* Starts automatically when executing `python etl_pipeline.py` via `if __name__ == "__main__":` entrypoint.
