
import json

from src.agents.data_analyst import run_data_analyst


result = run_data_analyst(
    store_id=1,
    product_id=793,
    date="2024-06-25"
)

print(json.dumps(result, indent=4))
