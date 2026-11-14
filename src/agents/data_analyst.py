
import json

from src.llm import get_llm
from src.skills.retail_skills import (
    load_retail_data,
    detect_stockout
)




SYSTEM_PROMPT = """
You are the Data Analyst agent of DemandLens AI.

Analyze only the supplied JSON evidence.

RULES:
- Report numerical values exactly as provided.
- Sales values are normalized.
- Never estimate hidden demand.
- Never speculate about customer behavior, shopping
  periods, online purchases or alternative stores.
- Never infer hourly sales from daily sales.
- Do not introduce external knowledge.
- Do not infer the daytime interval from total
  stockout hours.

RESPONSE FORMAT:

Observed facts:
Report recorded sales and stockout information.

Business implication:
If a stockout occurred, explain that recorded sales
may underestimate customer demand.

Limitations:
Explain that the supplied evidence cannot quantify
actual unmet demand.

Use a maximum of 100 words.
"""



def run_data_analyst(store_id, product_id, date):
    """Investigate retail data and interpret the results."""

    df = load_retail_data()

    result = detect_stockout(
        df,
        store_id,
        product_id,
        date
    )

    if result["status"] != "success":
        return {
            "agent": "data_analyst",
            "status": result["status"],
            "data": result,
            "analysis": result.get("message", "")
        }

    llm = get_llm()

    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", json.dumps(result, indent=2))
    ])

    return {
        "agent": "data_analyst",
        "status": "success",
        "data": result,
        "analysis": response.content,
        "token_usage": response.usage_metadata
    }
