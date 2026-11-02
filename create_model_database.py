import sqlite3
import pandas as pd

DB_URI = "file:////192.168.1.95/CS-CLASSROOM/intraday_5m.sqlite?mode=ro&immutable=1"

with sqlite3.connect(DB_URI, uri=True) as source:

    df = pd.read_sql_query(
        """
        SELECT symbol, ts_utc, close, volume
        FROM bars_5m
        WHERE symbol IN ('MSFT','DIS','WMT')
          AND ts_utc >= '2025-01-01'
          AND ts_utc < '2025-02-01'
        """,
        source,
    )

local_db = sqlite3.connect("model_data.db")

df.to_sql(
    "stock_data",
    local_db,
    if_exists="replace",
    index=False,
)

local_db.close()

print("Copied", len(df), "rows")
