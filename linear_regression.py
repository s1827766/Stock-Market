import sqlite3
import pandas as pd

conn = sqlite3.connect("model_data.db")

df = pd.read_sql_query(
    """
    SELECT *
    FROM stock_data
    ORDER BY symbol, ts_utc
""",
    conn,
)

conn.close()

df["ma20"] = df.groupby("symbol")["close"].transform(lambda x: x.rolling(20).mean())

df["future_close"] = df.groupby("symbol")["close"].shift(-12)

df = df.dropna()

df = df.sort_values("ts_utc")

split_index = int(len(df) * 0.8)

train_df = df.iloc[:split_index]
test_df = df.iloc[split_index:]

print("\nDataset Summary")
print("----------------")
print("Total rows:", len(df))
print("Training rows:", len(train_df))
print("Testing rows:", len(test_df))

print("\nTraining Sample:")
print(train_df.head())

print("\nTesting Sample:")
print(test_df.head())

output_conn = sqlite3.connect("regression_data.db")

train_df.to_sql("training_examples", output_conn, if_exists="replace", index=False)

test_df.to_sql("testing_examples", output_conn, if_exists="replace", index=False)

output_conn.close()

print("\nCreated regression_data.db")
print("Tables:")
print(" - training_examples")
print(" - testing_examples")
