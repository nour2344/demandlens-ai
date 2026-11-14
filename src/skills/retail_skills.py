
from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT_DIR / "data" / "raw" / "retail_sample.parquet"


def load_retail_data():
    """Load the local retail dataset."""
    df = pd.read_parquet(DATA_PATH)
    df["dt"] = pd.to_datetime(df["dt"])
    return df


def get_product_history(df, store_id, product_id):
    """Retrieve historical data for a store-product pair."""
    history = df[
        (df["store_id"] == store_id)
        & (df["product_id"] == product_id)
    ]

    return history.sort_values("dt").reset_index(drop=True)


def detect_stockout(df, store_id, product_id, date):
    """Investigate stock availability on a specific date."""
    history = get_product_history(df, store_id, product_id)

    record = history[history["dt"] == pd.Timestamp(date)]

    if record.empty:
        return {
            "status": "not_found",
            "message": "No matching record found."
        }

    if len(record) != 1:
        return {
            "status": "data_error",
            "message": "Duplicate records found."
        }

    row = record.iloc[0]
    hourly_status = row["hours_stock_status"]

    if len(hourly_status) != 24 or any(
        status not in (0, 1) for status in hourly_status
    ):
        return {
            "status": "data_error",
            "message": "Invalid hourly stock data."
        }

    stockout_hours = [
        hour
        for hour, status in enumerate(hourly_status)
        if status == 1
    ]

    return {
        "status": "success",
        "store_id": store_id,
        "product_id": product_id,
        "date": str(date),
        "recorded_sales": float(row["sale_amount"]),
        "stockout_detected": bool(stockout_hours),
        "total_stockout_hours": len(stockout_hours),
        "daytime_stockout_hours": int(row["stock_hour6_22_cnt"]),
        "stockout_hours": stockout_hours
    }
