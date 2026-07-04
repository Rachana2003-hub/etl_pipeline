import os
from urllib.parse import quote_plus

# Database configurations
DB_USER = os.getenv("ETL_DB_USER", "root")
DB_PASSWORD = os.getenv("ETL_DB_PASSWORD", "Rachana@03")
DB_HOST = os.getenv("ETL_DB_HOST", "localhost")
DB_PORT = int(os.getenv("ETL_DB_PORT", "3306"))
DB_NAME = os.getenv("ETL_DB_NAME", "etl_db")
DB_TABLE = "sales_transformed"

# File configurations
CSV_FILE_PATH = os.path.join("data", "sales.csv")
LOG_FILE_PATH = os.path.join("logs", "etl.log")

# Encode password safely
encoded_password = quote_plus(DB_PASSWORD)

# SQLAlchemy connection string (STRING, not URL object)
DB_CONNECTION_URL = (
    f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
