
import json

from src.llm import get_llm


VALID_ROUTES = {
    "data",
    "estimate",
    "knowledge",
    "hybrid",
    "clarify"
}


SYSTEM_PROMPT = """
You are the routing agent of DemandLens AI.

Classify the user's question into one route:

data:
Inspect recorded sales or stockout information.

estimate:
Estimate hidden or lost customer demand.

knowledge:
Answer a general scientific or methodological question.

hybrid:
Combine a specific retail investigation with
demand estimation and scientific explanation.

clarify:
The request is ambiguous or outside the system's scope.

Classify intent only.
Missing identifiers are checked separately by Python.
Do not answer the question or invent information.
"""


ROUTER_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "routing_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "route": {
                    "type": "string",
                    "enum": sorted(VALID_ROUTES)
                },
                "reason": {
                    "type": "string"
                }
            },
            "required": ["route", "reason"],
            "additionalProperties": False
        }
    }
}


def fallback_route(question):

    question = question.lower()

    estimation = any(
        phrase in question
        for phrase in (
            "estimate",
            "lost demand",
            "hidden demand",
            "unmet demand",
            "reconstruct"
        )
    )

    scientific = any(
        phrase in question
        for phrase in (
            "explain",
            "scientific",
            "forecasting implications",
            "what is",
            "why",
            "how do"
        )
    )

    if estimation and scientific:
        return "hybrid"

    if scientific:
        return "knowledge"

    if estimation:
        return "estimate"

    if any(
        phrase in question
        for phrase in (
            "stockout",
            "recorded sales",
            "availability",
            "in stock"
        )
    ):
        return "data"

    return "clarify"


def classify_request(question):

    usage = {}

    try:

        llm = get_llm().bind(
            response_format=ROUTER_SCHEMA
        )

        response = llm.invoke([
            ("system", SYSTEM_PROMPT),
            ("human", question)
        ])

        usage = response.usage_metadata or {}

        result = json.loads(response.content.strip())

        if result.get("route") not in VALID_ROUTES:
            raise ValueError("Invalid routing decision.")

        return {
            "route": result["route"],
            "reason": result["reason"],
            "routing_method": "llm",
            "token_usage": usage
        }

    except Exception as error:

        return {
            "route": fallback_route(question),
            "reason": "Rule-based fallback routing.",
            "routing_method": "deterministic_fallback",
            "error_type": type(error).__name__,
            "token_usage": usage
        }
