import argparse
import sqlite3
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from db_location import get_db_path


PREDICTOR_COLUMNS = [
    "momentum_1d",
    "momentum_5d",
    "momentum_20d",
    "volatility_5d",
    "volatility_20d",
    "price_vs_sma_5d",
    "price_vs_sma_20d",
]


def load_price_history(database_path: Path) -> pd.DataFrame:
    with sqlite3.connect(database_path) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(prices)")
        }
        if "ticker" not in columns:
            raise ValueError(f"The prices table in {database_path} needs a ticker column.")

        date_columns = [name for name in ("trade_date", "recorded_at") if name in columns]
        close_columns = [name for name in ("close", "price") if name in columns]
        if not date_columns or not close_columns:
            raise ValueError(
                "The prices table needs a trade_date or recorded_at column and a "
                "close or price column."
            )

        date_expression = _column_expression(date_columns)
        close_expression = _column_expression(close_columns)
        rows = connection.execute(
            f"SELECT rowid, ticker, {date_expression}, {close_expression} "
            "FROM prices ORDER BY rowid"
        ).fetchall()

    history = pd.DataFrame(rows, columns=["row_id", "ticker", "date", "close"])
    if history.empty:
        raise ValueError(f"No price records were found in {database_path}.")

    history["ticker"] = history["ticker"].astype(str).str.upper()
    history["date"] = pd.to_datetime(history["date"], errors="coerce", utc=True)
    history["date"] = history["date"].dt.tz_localize(None).dt.normalize()
    history["close"] = pd.to_numeric(history["close"], errors="coerce")
    history = history.dropna(subset=["ticker", "date", "close"])
    history = history[history["close"] > 0]
    history = history.sort_values(["ticker", "date", "row_id"])
    history = history.drop_duplicates(["ticker", "date"], keep="last")
    return history.drop(columns="row_id").reset_index(drop=True)


def _column_expression(columns: list[str]) -> str:
    quoted_columns = [f'"{name}"' for name in columns]
    if len(quoted_columns) == 1:
        return quoted_columns[0]
    return "COALESCE(" + ", ".join(quoted_columns) + ")"


def create_model_data(history: pd.DataFrame) -> pd.DataFrame:
    data = history.sort_values(["ticker", "date"]).copy()
    grouped_close = data.groupby("ticker", sort=False)["close"]
    data["momentum_1d"] = grouped_close.pct_change()
    data["momentum_5d"] = grouped_close.pct_change(periods=5)
    data["momentum_20d"] = grouped_close.pct_change(periods=20)

    grouped_returns = data.groupby("ticker", sort=False)["momentum_1d"]
    for window in (5, 20):
        data[f"volatility_{window}d"] = grouped_returns.transform(
            lambda returns: returns.rolling(window).std()
        )
        data[f"price_vs_sma_{window}d"] = data.groupby("ticker", sort=False)["close"].transform(
            lambda close: close / close.rolling(window).mean() - 1
        )

    data["next_day_return"] = data.groupby("ticker", sort=False)["close"].transform(
        lambda close: close.shift(-1) / close - 1
    )
    return data.dropna(subset=PREDICTOR_COLUMNS + ["next_day_return"])


def run_model(database_path: Path, test_fraction: float = 0.2) -> None:
    history = load_price_history(database_path)
    model_data = create_model_data(history)
    dates = model_data["date"].drop_duplicates().sort_values().to_list()
    split_index = int(len(dates) * (1 - test_fraction))
    if split_index < 1 or split_index >= len(dates):
        raise ValueError("Not enough dates for the requested chronological train/test split.")

    test_start = dates[split_index]
    train_rows = model_data[model_data["date"] < test_start]
    test_rows = model_data[model_data["date"] >= test_start]
    if len(train_rows) < 2 or test_rows.empty:
        raise ValueError("Not enough usable rows to train and evaluate the model.")

    feature_data = pd.get_dummies(
        model_data[PREDICTOR_COLUMNS + ["ticker"]],
        columns=["ticker"],
        drop_first=True,
        dtype=float,
    )
    train_features = feature_data.loc[train_rows.index]
    test_features = feature_data.loc[test_rows.index]
    train_target = train_rows["next_day_return"]
    test_target = test_rows["next_day_return"]

    model = LinearRegression()
    model.fit(train_features, train_target)
    # print("\nCoefficients:")
    # for name, coef in zip(train_features.columns, model.coef_):
    #     print(f"{name}: {coef}")
    predictions = model.predict(test_features)

    mae = mean_absolute_error(test_target, predictions)
    rmse = mean_squared_error(test_target, predictions) ** 0.5
    baseline_mae = mean_absolute_error(test_target, [0.0] * len(test_target))

    # print(f"Database: {database_path}")
    # print(f"Usable observations: {len(model_data)}")
    # print(f"Train observations: {len(train_rows)}")
    # print(f"Test observations: {len(test_rows)}")
    # print(f"Test period: {test_rows['date'].min().date()} to {test_rows['date'].max().date()}")
    # print(f"Test MAE: {mae:.6f} ({mae:.2%})")
    # print(f"Test RMSE: {rmse:.6f} ({rmse:.2%})")
    # print(f"Test R²: {r2_score(test_target, predictions):.4f}")
    # print(f"Zero-return baseline MAE: {baseline_mae:.6f} ({baseline_mae:.2%})")

    # print(predictions[0])

    # print(model.intercept_)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Predict each ticker's next-session return with linear regression."
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=None,
        help="SQLite database path (defaults to the project's trading database).",
    )
    parser.add_argument(
        "--test-fraction",
        type=float,
        default=0.2,
        help="Fraction of latest dates reserved for evaluation (default: 0.2).",
    )
    args = parser.parse_args()
    if not 0 < args.test_fraction < 1:
        parser.error("--test-fraction must be between 0 and 1.")
    database_path = args.database if args.database is not None else get_db_path()
    run_model(database_path.expanduser().resolve(), args.test_fraction)


if __name__ == "__main__":
    main()