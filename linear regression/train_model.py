import sqlite3
import pandas as pd

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score

conn = sqlite3.connect("linear regression/regression_data.db")

train_df = pd.read_sql_query("SELECT * FROM training_examples", conn)
test_df = pd.read_sql_query("SELECT * FROM testing_examples", conn)

conn.close()

X_train = train_df[["ma5", "ma10", "ma20", "ma50"]]
y_train = train_df["future_return"]

X_test = test_df[["ma5", "ma10", "ma20", "ma50"]]
y_test = test_df["future_return"]

model = LinearRegression()
model.fit(X_train, y_train)

predictions = model.predict(X_test)

mae = mean_absolute_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

print("\nModel Results")
print("----------------")
print("Mean Absolute Error:", round(mae, 4))
print("R-squared:", round(r2, 4))

results = test_df.copy()
results["prediction"] = predictions

print("\nSample Predictions")
print(results[["symbol", "close", "future_return", "prediction"]].head(20))

results["buy_signal"] = results["prediction"] > 0.0025

print("\nBuy Signals")
print(results[["symbol", "close", "prediction", "buy_signal"]].head(20))

print("\nCoefficients")
for feature, coef in sorted(
    zip(X_train.columns, model.coef_),
    key=lambda item: abs(item[1]),
    reverse=True,
):
    print(f"{feature} | {coef:.6e}")
