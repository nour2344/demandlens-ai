
import json
from pathlib import Path

from src.agents.knowledge_agent import run_knowledge_agent
from src.agents.quality_controller import run_quality_controller
from src.skills.validation_skills import validate_citations


ROOT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT_DIR / "evaluation" / "results"

QUESTION = (
    "How do stockouts affect retail demand forecasting, "
    "and why is correcting censored demand important?"
)

CONFIGURATIONS = [3, 8]


def evaluate_context():

    results = []

    for top_k in CONFIGURATIONS:

        print("\n" + "=" * 60)
        print(f"CONTEXT CONFIGURATION: TOP_K = {top_k}")
        print("=" * 60)

        result = run_knowledge_agent(
            question=QUESTION,
            top_k=top_k
        )

        sources = result.get("sources", [])
        analysis = result.get("analysis", "")

        citation_issues = validate_citations(
            analysis, sources
        )

        quality = run_quality_controller([result])

        usage = result.get("token_usage") or {}
        quality_usage = quality.get("token_usage") or {}

        unique_documents = {
            source["source"]
            for source in sources
        }

        unique_pages = {
            (source["source"], source["page"])
            for source in sources
        }

        evaluation = {
            "top_k": top_k,
            "status": result["status"],
            "retrieved_passages": len(sources),
            "unique_documents": len(unique_documents),
            "unique_pages": len(unique_pages),
            "context_characters": result.get(
                "context_characters", 0
            ),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_seconds": result.get("latency_seconds"),
            "quality_approved": quality.get("approved", False),
            "quality_status": quality.get("status"),
            "quality_issues": quality.get("issues", []),
            "verification_tokens": quality_usage.get(
                "total_tokens", 0
            ),
            "citation_issues": citation_issues,
            "answer": analysis,
            "sources": sources
        }

        results.append(evaluation)

        display_result = {
            key: value
            for key, value in evaluation.items()
            if key != "sources"
        }

        print(json.dumps(display_result, indent=4))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "question": QUESTION,
        "configurations": results
    }

    with open(
        OUTPUT_DIR / "context_evaluation.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(report, file, indent=4)

    print("\n===== CONTEXT COMPARISON =====")

    for result in results:

        print(
            f"top_k={result['top_k']} | "
            f"Tokens={result['total_tokens']} | "
            f"Latency={result['latency_seconds']}s | "
            f"Approved={result['quality_approved']}"
        )


if __name__ == "__main__":
    evaluate_context()
