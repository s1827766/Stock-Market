# Add this table inside create_database() after the prices table.
SIGNALS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    recorded_at TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL
)
"""

# Add this function to database_manager.py.
def save_signal(connection_factory, ticker, recorded_at, decision, reason):
    connection = connection_factory()
    connection.execute(
        """
        INSERT INTO signals (ticker, recorded_at, decision, reason)
        VALUES (?, ?, ?, ?)
        """,
        (ticker, recorded_at, decision, reason),
    )
    connection.commit()
    connection.close()
