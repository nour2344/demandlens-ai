
import json

from src.skills.retail_skills import (
    load_retail_data,
    detect_stockout
)


df = load_retail_data()

result = detect_stockout(
    df,
    store_id=0,
    product_id=38,
    date="2024-04-09"
)

print(json.dumps(result, indent=4))
