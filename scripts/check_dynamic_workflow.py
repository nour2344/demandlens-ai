
import json
from time import perf_counter

from src.workflows.dynamic_workflow import (
    build_dynamic_workflow
)


workflow = build_dynamic_workflow()


test_cases = [

    {
        "name": "DATA INVESTIGATION",
        "question": "Did this product experience a stockout?",
        "store_id": 1,
        "product_id": 793,
        "date": "2024-06-25"
    },

    {
        "name": "DEMAND ESTIMATION",
        "question": "Estimate the hidden demand for this product.",
        "store_id": 1,
        "product_id": 793,
        "date": "2024-06-25"
    },

    {
        "name": "SCIENTIFIC QUESTION",
        "question": "What is censored demand in retail?"
    },

    {
        "name": "INSUFFICIENT EVIDENCE",
        "question": "Estimate lost demand for this product.",
        "store_id": 0,
        "product_id": 72,
        "date": "2024-06-25"
    },

    {
        "name": "MISSING INFORMATION",
        "question": "Estimate lost demand for my product."
    },

    {
        "name": "HYBRID INVESTIGATION",
        "question": (
            "Estimate lost demand for this product and "
            "explain the scientific forecasting implications."
        ),
        "store_id": 1,
        "product_id": 793,
        "date": "2024-06-25"
    }
]


for case in test_cases:

    print("\n" + "=" * 60)
    print(case["name"])
    print("=" * 60)

    initial_state = {
        key: value
        for key, value in case.items()
        if key != "name"
    }

    initial_state.update({
        "top_k": 3,
        "execution_trace": [],
        "retry_count": 0,
        "retry_tokens": 0
    })

    start = perf_counter()

    result = workflow.invoke(initial_state)

    elapsed = perf_counter() - start

    print("Route:", result.get("route"))

    print(
        "Execution trace:",
        " -> ".join(result["execution_trace"])
    )

    print("\nQuality control:")

    print(json.dumps(
        result.get("quality_result", {}),
        indent=4
    ))

    print("\nFinal answer:")
    print(result["final_answer"])

    print("\nTotal tokens:", result["total_tokens"])
    print("Latency:", round(elapsed, 3), "seconds")
