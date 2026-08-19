"""
DAY 2 STARTER EXAMPLE

IMPORTANT:
- Do NOT replace your working Alpaca project with this file.
- Find the place where your existing strategy ALREADY downloads historical bars.
- Add ONE loop that saves those existing bars to the database.
- Do NOT change the strategy or add a new trading rule.
"""

from database_manager import create_database, save_price

create_database()

# ------------------------------------------------------------------
# OPTION A: Your existing Alpaca code gives you a pandas DataFrame.
# Many projects have code similar to:
#
#     bars = client.get_stock_bars(...).df
#
# If your existing variable is a DataFrame, adapt this pattern.
# ------------------------------------------------------------------


def save_dataframe_prices(ticker, bars_dataframe):
    """Save the historical bars your program already downloaded."""

    for timestamp, row in bars_dataframe.iterrows():
        save_price(
            ticker=ticker,
            recorded_at=str(timestamp),
            price=float(row["close"]),
        )


# ------------------------------------------------------------------
# OPTION B: Your existing Alpaca code gives you Bar objects in a list.
# If your existing variable contains objects with .timestamp and .close,
# adapt this pattern instead.
# ------------------------------------------------------------------


def save_bar_objects(ticker, bars):
    """Save historical Bar objects your program already downloaded."""

    for bar in bars:
        save_price(
            ticker=ticker,
            recorded_at=str(bar.timestamp),
            price=float(bar.close),
        )


# ------------------------------------------------------------------
# WHAT YOU ACTUALLY DO IN YOUR PROJECT
# ------------------------------------------------------------------
# 1. Find the variable that already contains the price history used by
#    your algorithm.
# 2. Choose the pattern above that matches your data.
# 3. Call it AFTER Alpaca returns the data and BEFORE/AROUND the place
#    where your strategy uses that same data.
#
# Example only:
#
# ticker = "AAPL"
# bars = YOUR_EXISTING_ALPACA_HISTORY_VARIABLE
# save_dataframe_prices(ticker, bars)
#
# decision = run_your_existing_strategy(bars)
#
# Your existing strategy continues unchanged.
