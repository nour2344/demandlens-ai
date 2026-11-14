
import json
from pathlib import Path
from time import perf_counter

from src.workflows.dynamic_workflow import (
    build_dynamic_workflow
)


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "evaluation" / "results"


TEST_CASES = [
    {
        "name": "data_investigation",
        "input": {
            "question": "Did this product experience a stockout?",
            "store_id": 1,
            "product_id": 793,
            "date": "2024-06-25"
        },
        "expected_route": "data",
        "expected_trace": [
            "router", "data_analyst",
            "quality_controller", "final_response"
        ],
        "expected_outcome": "approved"
    },
    {
        "name": "demand_estimation",
        "input": {
            "question": "Estimate the hidden demand for this product.",
            "store_id": 1,
            "product_id": 793,
            "date": "2024-06-25"
        },
        "expected_route": "estimate",
        "expected_trace": [
            "router", "data_analyst",
            "demand_estimator", "quality_controller",
            "final_response"
        ],
        "expected_outcome": "approved"
    },
    {
        "name": "scientific_question",
        "input": {
            "question": "What is censored demand in retail?"
        },
        "expected_route": "knowledge",
        "expected_trace": [
            "router", "knowledge_agent",
            "quality_controller", "final_response"
        ],
        "expected_outcome": "approved"
    },
    {
        "name": "insufficient_evidence",
        "input": {
            "question": "Estimate lost demand for this product.",
            "store_id": 0,
            "product_id": 72,
            "date": "2024-06-25"
        },
        "expected_route": "estimate",
        "expected_trace": [
            "router", "data_analyst",
            "demand_estimator", "quality_controller",
            "final_response"
        ],
        "expected_outcome": "insufficient_evidence"
    },
    {
        "name": "missing_information",
        "input": {
            "question": "Estimate lost demand for my product."
        },
        "expected_route": "clarify",
        "expected_trace": [
            "router", "clarification"
        ],
        "expected_outcome": "clarification"
    },
    {
        "name": "hybrid_investigation",
        "input": {
            "question": (
                "Estimate lost demand for this product "
                "and explain the scientific forecasting implications."
            ),
            "store_id": 1,
            "product_id": 793,
            "date": "2024-06-25"
        },
        "expected_route": "hybrid",
        "expected_trace": [
            "router", "data_analyst",
            "demand_estimator", "knowledge_agent",
            "quality_controller", "final_response"
        ],
        "expected_outcome": "approved"
    }
]


def get_outcome(result):

    if "clarification" in result.get("execution_trace", []):
        return "clarification"

    quality = result.get("quality_result", {})

    if quality.get("approved") is not True:
        return quality.get("status", "verification_error")

    demand = result.get("demand_result", {})

    if demand.get("status") == "insufficient_evidence":
        return "insufficient_evidence"

    return "approved"


def evaluate_workflows():

    workflow = build_dynamic_workflow()

    results = []

    for case in TEST_CASES:

        print(f"\nEvaluating: {case['name']}")

        state = {
            **case["input"],
            "top_k": 3,
            "execution_trace": [],
            "retry_count": 0,
            "retry_tokens": 0
        }

        start = perf_counter()

        result = workflow.invoke(state)

        latency = perf_counter() - start

        outcome = get_outcome(result)

        route_correct = (
            result.get("route") == case["expected_route"]
        )

        trace_correct = (
            result.get("execution_trace")
            == case["expected_trace"]
        )

        outcome_correct = (
            outcome == case["expected_outcome"]
        )

        evaluation = {
            "case": case["name"],
            "expected_route": case["expected_route"],
            "actual_route": result.get("route"),
            "route_correct": route_correct,
            "expected_trace": case["expected_trace"],
            "actual_trace": result.get("execution_trace"),
            "trace_correct": trace_correct,
            "expected_outcome": case["expected_outcome"],
            "actual_outcome": outcome,
            "outcome_correct": outcome_correct,
            "passed": (
                route_correct
                and trace_correct
                and outcome_correct
            ),
            "tokens": result.get("total_tokens", 0),
            "latency_seconds": round(latency, 3),
            "quality_issues": result.get(
                "quality_result", {}
            ).get("issues", []),
            "final_answer": result.get("final_answer", "")
        }

        results.append(evaluation)

        print("PASS" if evaluation["passed"] else "FAIL")

    n = len(results)

    summary = {
        "total_cases": n,
        "passed_cases": sum(r["passed"] for r in results),
        "routing_accuracy": (
            sum(r["route_correct"] for r in results) / n
        ),
        "execution_path_accuracy": (
            sum(r["trace_correct"] for r in results) / n
        ),
        "outcome_accuracy": (
            sum(r["outcome_correct"] for r in results) / n
        ),
        "overall_pass_rate": (
            sum(r["passed"] for r in results) / n
        ),
        "average_tokens": (
            sum(r["tokens"] for r in results) / n
        ),
        "average_latency_seconds": (
            sum(r["latency_seconds"] for r in results) / n
        )
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "summary": summary,
        "results": results
    }

    with open(
        OUTPUT_DIR / "workflow_evaluation.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(report, file, indent=4)

    print("\n===== WORKFLOW EVALUATION =====")
    print(json.dumps(summary, indent=4))


if __name__ == "__main__":
    evaluate_workflows()
