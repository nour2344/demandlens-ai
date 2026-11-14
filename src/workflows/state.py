
from typing import TypedDict


class InvestigationState(TypedDict, total=False):

    # User input
    question: str
    store_id: int
    product_id: int
    date: str
    top_k: int

    # Agent outputs
    data_result: dict
    demand_result: dict
    knowledge_result: dict
    quality_result: dict

    # Workflow information
    route: str
    execution_trace: list[str]

    # Final output
    final_answer: str
    total_tokens: int

    # Dynamic routing
    router_result: dict
    clarification: str

    # Recovery mechanism
    retry_count: int
    retry_tokens: int
    verification_feedback: str
