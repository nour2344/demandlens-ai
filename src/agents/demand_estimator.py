
import json

from src.llm import get_llm
from src.skills.retail_skills import load_retail_data
from src.skills.demand_skills import estimate_hidden_demand



SYSTEM_PROMPT = """
You are the Demand Estimator agent of DemandLens AI.

Interpret only the supplied JSON evidence.

RULES:
- Preserve all numerical values.
- Express values as normalized sales.
- Distinguish estimated demand from observed demand.
- Do not perform additional calculations.
- Do not invent confidence scores.
- Do not speculate about staffing, promotions,
  customer behavior or financial impact.
- Zero estimated lost demand does not prove
  that no actual demand was lost.

RESPONSE FORMAT:

Demand estimation:
Report recorded sales, estimated lost demand
and estimated total demand.

Business implication:
Explain how stockouts may cause observed sales
to underestimate potential demand.

Limitations:
State the estimation method and the limited
historical evidence.

Use a maximum of 100 words.
"""



def run_demand_estimator(store_id, product_id, date):
    """Estimate and interpret hidden customer demand."""

    df = load_retail_data()

    result = estimate_hidden_demand(
        df,
        store_id,
        product_id,
        date
    )

    if result["status"] != "success":
        return {
            "agent": "demand_estimator",
            "status": result["status"],
            "data": result,
            "analysis": result.get(
                "message",
                "No daytime stockout detected."
            )
        }

    llm = get_llm()

    response = llm.invoke([
        ("system", SYSTEM_PROMPT),
        ("human", json.dumps(result, indent=2))
    ])

    return {
        "agent": "demand_estimator",
        "status": "success",
        "data": result,
        "analysis": response.content,
        "token_usage": response.usage_metadata
    }
