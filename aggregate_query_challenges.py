"""
Type ONE required aggregate query at a time below, then run this file.
Do this 5 times total, once per required challenge -- replace the query,
save, run, screenshot the output, then move to the next challenge.

aggregate_queries.py is a reference/answer-check file. Do not open it
until you've written and run your own version of each query below.

Your 5 required challenges (see the Day 3 Material for full wording):
  1. Average trade_price, across all trades.
  2. Lowest and highest trade_price.
  3. Total shares (quantity) traded, per ticker (needs GROUP BY).
  4. Tickers with more than 1 trade (needs GROUP BY + HAVING).
  5. One original aggregate query about your own data.
"""
import sqlite3
from db_location import get_db_path

DB = get_db_path()

# Replace ONLY the SQL below after you have written/predicted it on paper.
# This starts as the worked example from the Material (challenge 0, free).
queries = {
  "avg_trade_price": "SELECT AVG(trade_price) FROM trades;",
  "min_max_trade_price": "SELECT MIN(trade_price), MAX(trade_price) FROM trades;",
  "total_quantity_per_ticker": "SELECT ticker, SUM(quantity) FROM trades GROUP BY ticker;",
  "tickers_with_more_than_one_trade": "SELECT ticker, COUNT(*) FROM trades GROUP BY ticker HAVING COUNT(*) > 1;",
  "my_original_query": "SELECT ticker, AVG(trade_price) FROM trades GROUP BY ticker HAVING AVG(trade_price) > 100;",
}

with sqlite3.connect(DB) as con:
    for name, query in queries.items():
        print(f"\n--- {name} ---")
        for row in con.execute(query):
            print(row)