
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]

REPORT_PATH = (
    ROOT_DIR
    / "evaluation"
    / "results"
    / "workflow_evaluation.json"
)


with open(REPORT_PATH, encoding="utf-8") as file:
    report = json.load(file)


for result in report["results"]:

    if result["passed"]:
        continue

    print("\n" + "=" * 60)
    print("FAILED CASE:", result["case"])
    print("=" * 60)

    print("\nExpected route:", result["expected_route"])
    print("Actual route:", result["actual_route"])

    print("\nExpected execution path:")
    print(" -> ".join(result["expected_trace"]))

    print("\nActual execution path:")
    print(" -> ".join(result["actual_trace"] or []))

    print("\nExpected outcome:", result["expected_outcome"])
    print("Actual outcome:", result["actual_outcome"])

    print("\nQuality issues:")

    for issue in result["quality_issues"]:
        print("-", issue)

    print("\nFinal answer:")
    print(result["final_answer"])
