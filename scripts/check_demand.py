
import json

from src.skills.retail_skills import load_retail_data
from src.skills.demand_skills import estimate_hidden_demand


df = load_retail_data()

result = estimate_hidden_demand(
    df,
    store_id=0,
    product_id=38,
    date="2024-06-01"
)

print(json.dumps(result, indent=4))
