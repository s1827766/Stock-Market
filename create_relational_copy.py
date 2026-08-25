"""Rebuild a clean relational learning copy: stocks + relational_prices."""
import sqlite3
from db_location import get_db_path

DB = get_db_path()
with sqlite3.connect(DB) as con:
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("DROP TABLE IF EXISTS relational_prices")
    con.execute("DROP TABLE IF EXISTS stocks")

    con.execute("""
        CREATE TABLE stocks (
            stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE NOT NULL,
            company_name TEXT
        )
    """)
    con.execute("""
        CREATE TABLE relational_prices (
            price_id INTEGER PRIMARY KEY AUTOINCREMENT,
            stock_id INTEGER NOT NULL,
            trade_date TEXT NOT NULL,
            close REAL NOT NULL,
            FOREIGN KEY(stock_id) REFERENCES stocks(stock_id)
        )
    """)

    for (ticker,) in con.execute("SELECT DISTINCT ticker FROM prices"):
        con.execute("INSERT INTO stocks (ticker) VALUES (?)", (ticker,))

    price_rows = con.execute("SELECT ticker, trade_date, close FROM prices").fetchall()
    for ticker, trade_date, close in price_rows:
        stock_id = con.execute("SELECT stock_id FROM stocks WHERE ticker = ?", (ticker,)).fetchone()[0]
        con.execute(
            "INSERT INTO relational_prices (stock_id, trade_date, close) VALUES (?, ?, ?)",
            (stock_id, trade_date, close),
        )

print(f"Relational learning copy rebuilt in {DB}")
