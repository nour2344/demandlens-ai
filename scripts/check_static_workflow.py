
import json
from time import perf_counter

from src.workflows.static_workflow import (
    build_static_workflow
)


workflow = build_static_workflow()

initial_state = {
    "question": (
        "Investigate the impact of stockouts on retail "
        "demand and explain the forecasting implications."
    ),
    "store_id": 1,
    "product_id": 793,
    "date": "2024-06-25",
    "top_k": 3,
    "execution_trace": []
}

start = perf_counter()

result = workflow.invoke(initial_state)

elapsed = perf_counter() - start


print("\n===== EXECUTION TRACE =====")

for index, node in enumerate(
    result["execution_trace"], start=1
):
    print(f"{index}. {node}")

print("\n===== KNOWLEDGE AGENT OUTPUT =====")

print(json.dumps(
    result.get("knowledge_result", {}),
    indent=4
))

print("\n===== QUALITY CONTROL =====")
print(json.dumps(result["quality_result"], indent=4))


print("\n===== FINAL RESPONSE =====")
print(result["final_answer"])


print("\n===== PERFORMANCE =====")
print("Total tokens:", result["total_tokens"])
print("Execution time:", round(elapsed, 3), "seconds")

