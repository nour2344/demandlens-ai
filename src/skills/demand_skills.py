
import numpy as np
import pandas as pd

from src.skills.retail_skills import (
    get_product_history,
    detect_stockout
)


MIN_COMPARABLE_DAYS = 3


def valid_hourly_data(row):
    """Check the integrity of hourly sales and stock data."""
    try:
        sales = np.asarray(row["hours_sale"], dtype=float)
        stock = np.asarray(row["hours_stock_status"], dtype=float)

        return bool(
            sales.shape == (24,)
            and stock.shape == (24,)
            and np.isfinite(sales).all()
            and (sales >= 0).all()
            and np.isin(stock, [0, 1]).all()
        )
    except (TypeError, ValueError):
        return False


def estimate_hidden_demand(df, store_id, product_id, date):
    """Estimate unmet demand using comparable historical hours."""

    investigation = detect_stockout(
        df, store_id, product_id, date
    )

    if investigation["status"] != "success":
        return investigation

    history = get_product_history(df, store_id, product_id)
    target_date = pd.Timestamp(date)

    target = history[history["dt"] == target_date].iloc[0]

    if not valid_hourly_data(target):
        return {
            "status": "data_error",
            "message": "Invalid hourly data."
        }

    # Only investigate daytime hours: 06:00 to 22:00.
    stockout_hours = [
        h for h in investigation["stockout_hours"]
        if 6 <= h < 22
    ]

    if not stockout_hours:
        return {
            "status": "no_daytime_stockout",
            "estimated_lost_demand": 0.0
        }

    # Only use past observations under similar conditions.
    historical = history[
        (history["dt"] < target_date)
        & (history["holiday_flag"] == target["holiday_flag"])
        & (history["activity_flag"] == target["activity_flag"])
        & np.isclose(history["discount"], target["discount"])
    ]

    comparable_days = [
        row for _, row in historical.iterrows()
        if valid_hourly_data(row)
    ]

    hourly_estimates = []
    unsupported_hours = []

    for hour in stockout_hours:

        comparable_sales = [
            float(row["hours_sale"][hour])
            for row in comparable_days
            if row["hours_stock_status"][hour] == 0
        ]

        if len(comparable_sales) < MIN_COMPARABLE_DAYS:
            unsupported_hours.append(hour)
            continue

        expected_sales = float(np.mean(comparable_sales))
        actual_sales = float(target["hours_sale"][hour])

        lost_demand = max(0.0, expected_sales - actual_sales)

        hourly_estimates.append({
            "hour": hour,
            "actual_sales": round(actual_sales, 4),
            "expected_sales": round(expected_sales, 4),
            "estimated_lost_demand": round(lost_demand, 4),
            "comparable_observations": len(comparable_sales)
        })

    if unsupported_hours:
        return {
            "status": "insufficient_evidence",
            "message": "Not enough comparable historical data.",
            "unsupported_hours": unsupported_hours,
            "hourly_estimates": hourly_estimates,
            "estimated_lost_demand": None
        }

    total_lost = sum(
        item["estimated_lost_demand"]
        for item in hourly_estimates
    )

    return {
        "status": "success",
        "store_id": store_id,
        "product_id": product_id,
        "date": str(date),
        "recorded_sales": investigation["recorded_sales"],
        "estimated_lost_demand": round(total_lost, 4),
        "estimated_total_demand": round(
            investigation["recorded_sales"] + total_lost, 4
        ),
        "hourly_estimates": hourly_estimates,
        "method": "Comparable historical hourly average",
        "unit": "Normalized sales"
    }
