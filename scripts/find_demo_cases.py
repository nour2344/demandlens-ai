
import json

from src.skills.retail_skills import load_retail_data
from src.skills.demand_skills import estimate_hidden_demand


df = load_retail_data()

candidates = df[
    df["stock_hour6_22_cnt"] > 0
].sort_values("dt", ascending=False)

found_cases = {}

for _, row in candidates.iterrows():

    result = estimate_hidden_demand(
        df,
        store_id=int(row["store_id"]),
        product_id=int(row["product_id"]),
        date=row["dt"].strftime("%Y-%m-%d")
    )

    status = result["status"]

    if status == "success":
        if result["estimated_lost_demand"] <= 0:
            continue

    if status in ("success", "insufficient_evidence"):
        if status not in found_cases:

            found_cases[status] = {
                "store_id": int(row["store_id"]),
                "product_id": int(row["product_id"]),
                "date": row["dt"].strftime("%Y-%m-%d"),
                "result": result
            }

    if len(found_cases) == 2:
        break

print(json.dumps(found_cases, indent=4))
