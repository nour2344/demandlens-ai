
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.skills.retail_skills import load_retail_data

from src.skills.demand_skills import (
    estimate_hidden_demand,
    valid_hourly_data
)


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "evaluation" / "results"

N_CASES = 100
RANDOM_SEED = 42
MASK_DURATION = 3


def calculate_metrics(actual, predicted):

    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)

    errors = predicted - actual

    return {
        "mae": float(np.mean(np.abs(errors))),
        "rmse": float(np.sqrt(np.mean(errors ** 2))),
        "wape": (
            float(
                np.sum(np.abs(errors))
                / np.sum(np.abs(actual)) * 100
            )
            if np.sum(np.abs(actual)) > 0
            else None
        ),
        "bias": float(np.mean(errors))
    }


def evaluate_demand():

    df = load_retail_data()

    rng = np.random.default_rng(RANDOM_SEED)

    candidates = df[
        df["dt"] >= df["dt"].min()
        + pd.Timedelta(days=30)
    ]

    eligible = []

    for index, row in candidates.iterrows():

        if not valid_hourly_data(row):
            continue

        stock = np.asarray(row["hours_stock_status"])

        # Select days without daytime stockouts
        if np.all(stock[6:22] == 0):
            eligible.append(index)

    if not eligible:
        raise ValueError("No eligible evaluation cases.")

    selected = rng.choice(
        eligible,
        size=min(N_CASES, len(eligible)),
        replace=False
    )

    results = []

    for index in selected:

        row = df.loc[index]

        start_hour = int(
            rng.integers(6, 22 - MASK_DURATION + 1)
        )

        masked_hours = list(
            range(start_hour, start_hour + MASK_DURATION)
        )

        sales = np.asarray(
            row["hours_sale"], dtype=float
        ).copy()

        stock = np.asarray(
            row["hours_stock_status"]
        ).copy()

        actual_hidden_sales = float(
            sales[masked_hours].sum()
        )

        # Simulate unavailable inventory
        sales[masked_hours] = 0.0
        stock[masked_hours] = 1

        simulated = df.copy()

        simulated.at[index, "hours_sale"] = sales
        simulated.at[index, "hours_stock_status"] = stock

        simulated.at[index, "sale_amount"] = max(
            0.0,
            float(row["sale_amount"]) - actual_hidden_sales
        )

        simulated.at[index, "stock_hour6_22_cnt"] = (
            MASK_DURATION
        )

        result = estimate_hidden_demand(
            simulated,
            int(row["store_id"]),
            int(row["product_id"]),
            row["dt"].strftime("%Y-%m-%d")
        )

        results.append({
            "store_id": int(row["store_id"]),
            "product_id": int(row["product_id"]),
            "date": row["dt"].strftime("%Y-%m-%d"),
            "masked_hours": masked_hours,
            "actual_hidden_sales": actual_hidden_sales,
            "estimated_hidden_demand": (
                result.get("estimated_lost_demand")
            ),
            "status": result["status"]
        })

    results_df = pd.DataFrame(results)

    successful = results_df[
        results_df["status"] == "success"
    ]

    summary = {
        "evaluation_cases": len(results_df),
        "successful_estimations": len(successful),
        "abstentions": int(
            (results_df["status"] == "insufficient_evidence").sum()
        ),
        "coverage_percentage": (
            len(successful) / len(results_df) * 100
        ),
        "random_seed": RANDOM_SEED,
        "mask_duration_hours": MASK_DURATION
    }

    if not successful.empty:

        actual = successful[
            "actual_hidden_sales"
        ].to_numpy()

        predicted = successful[
            "estimated_hidden_demand"
        ].to_numpy()

        summary["demand_estimator"] = calculate_metrics(
            actual, predicted
        )

        summary["zero_demand_baseline"] = calculate_metrics(
            actual, np.zeros_like(actual)
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results_df.to_csv(
        OUTPUT_DIR / "demand_evaluation.csv",
        index=False
    )

    with open(
        OUTPUT_DIR / "demand_metrics.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(summary, file, indent=4)

    print("\n===== DEMAND EVALUATION =====")
    print(json.dumps(summary, indent=4))

    return summary


if __name__ == "__main__":
    evaluate_demand()
