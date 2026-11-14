
import json

from src.llm import get_llm
from src.skills.retail_skills import (
    load_retail_data,
    detect_stockout
)



SYSTEM_PROMPT = """
You are the Data Analyst agent of DemandLens AI.

Your responsibility is to investigate recorded retail
sales and stock availability.

Strict rules:
- Use only the supplied analytical results.
- Never invent figures or stockout hours.
- Sales values are normalized, not physical quantities.
- Do not estimate hidden demand yourself.
- Do not assume customer traffic or purchasing behavior.
- A stockout does not necessarily mean zero sales.
- Distinguish confirmed facts from possible implications.
- Do not claim that information is absent from the
  entire dataset simply because it is not supplied.
- Do not make unsupported causal claims.

Provide a concise analysis with three sections:
1. Observed facts
2. Potential business implications
3. Limitations

Use no more than 150 words.
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
