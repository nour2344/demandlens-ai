
import json
from copy import deepcopy

from src.agents.quality_controller import run_quality_controller


valid_data = {
    "status": "success",
    "recorded_sales": 1.2,
    "estimated_lost_demand": 0.2667,
    "estimated_total_demand": 1.4667,
    "hourly_estimates": [
        {
            "hour": 19,
            "estimated_lost_demand": 0.0667,
            "comparable_observations": 3
        },
        {
            "hour": 20,
            "estimated_lost_demand": 0.1,
            "comparable_observations": 3
        },
        {
            "hour": 21,
            "estimated_lost_demand": 0.1,
            "comparable_observations": 3
        }
    ],
    "unit": "Normalized sales",
    "method": "Comparable historical hourly average"
}

valid_result = {
    "agent": "demand_estimator",
    "status": "success",
    "data": valid_data,
    "analysis": (
        "Recorded sales were 1.2 on a normalized scale. "
        "Estimated lost demand was 0.2667 and estimated "
        "total demand was 1.4667. "
        "The estimate relies on three comparable observations "
        "per hour and does not establish actual lost demand."
    )
}


print("\n===== CASE 1: VALID ANALYSIS =====")

print(json.dumps(
    run_quality_controller([valid_result]),
    indent=4
))


print("\n===== CASE 2: INCORRECT NUMBERS =====")

incorrect = deepcopy(valid_result)
incorrect["data"]["estimated_total_demand"] = 9.5

print(json.dumps(
    run_quality_controller([incorrect]),
    indent=4
))


print("\n===== CASE 3: UNSUPPORTED CONCLUSIONS =====")

hallucination = deepcopy(valid_result)

hallucination["analysis"] += (
    " Customers purchased from competitors, resulting "
    "in a proven financial loss of 500 dollars."
)

print(json.dumps(
    run_quality_controller([hallucination]),
    indent=4
))


print("\n===== CASE 4: INVENTED CITATION =====")

invalid_citation = {
    "agent": "knowledge_agent",
    "status": "success",
    "analysis": "Stockouts may suppress recorded sales [S9].",
    "sources": [
        {
            "citation_id": "S1",
            "text": "Stockouts can censor recorded demand."
        }
    ]
}

print(json.dumps(
    run_quality_controller([invalid_citation]),
    indent=4
))
