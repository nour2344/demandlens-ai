
import json

from src.agents.demand_estimator import run_demand_estimator


print("\n===== CASE 1: SUCCESS =====")

success = run_demand_estimator(
    store_id=1,
    product_id=793,
    date="2024-06-25"
)

print(json.dumps(success, indent=4))


print("\n===== CASE 2: INSUFFICIENT EVIDENCE =====")

failure = run_demand_estimator(
    store_id=0,
    product_id=72,
    date="2024-06-25"
)

print(json.dumps(failure, indent=4))
