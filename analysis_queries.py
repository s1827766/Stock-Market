import sqlite3

connection = sqlite3.connect("trading.db")

queries = {
    "total_prices": "SELECT COUNT(*) FROM prices",
    "highest_price": "SELECT MAX(price) FROM prices",
    "signals_by_type": """
        SELECT decision, COUNT(*)
        FROM signals
        GROUP BY decision
    """,
}

for name, query in queries.items():
    print("\n" + name)
    for row in connection.execute(query).fetchall():
        print(row)

connection.close()
