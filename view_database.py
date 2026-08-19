import sqlite3

connection = sqlite3.connect("trading.db")

cursor = connection.execute(
    """
    SELECT id, ticker, recorded_at, price
    FROM prices
    ORDER BY recorded_at
    """
)

for row in cursor.fetchall():
    print(row)

connection.close()
