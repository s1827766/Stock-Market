"""JOIN preview. Students should annotate the clauses before running it."""
import sqlite3
from db_location import get_db_path

DB = get_db_path()
query = """
SELECT prices.ticker,
       prices.trade_date,
       prices.close,
       trades.side,
       trades.quantity,
       trades.trade_price
FROM prices
JOIN trades
  ON prices.ticker = trades.ticker
 AND prices.trade_date = trades.trade_date
ORDER BY prices.trade_date;
"""

with sqlite3.connect(DB) as con:
    rows = con.execute(query).fetchall()
print(f"JOIN returned {len(rows)} rows")
for row in rows:
    print(row)
