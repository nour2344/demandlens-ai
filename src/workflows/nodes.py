
from src.workflows.state import InvestigationState

from src.agents.data_analyst import run_data_analyst
from src.agents.demand_estimator import run_demand_estimator
from src.agents.knowledge_agent import run_knowledge_agent
from src.agents.quality_controller import run_quality_controller


def execute_agent(state, name, result_key, function, **kwargs):
    """Execute an agent and record its result."""

    try:
        result = function(**kwargs)

    except Exception as error:
        result = {
            "agent": name,
            "status": "execution_error",
            "analysis": "Agent execution failed.",
            "error_type": type(error).__name__
        }

    return {
        result_key: result,
        "execution_trace": [
            *state.get("execution_trace", []),
            name
        ]
    }


def data_analyst_node(state: InvestigationState):

    return execute_agent(
        state,
        "data_analyst",
        "data_result",
        run_data_analyst,
        store_id=state["store_id"],
        product_id=state["product_id"],
        date=state["date"]
    )


def demand_estimator_node(state: InvestigationState):

    return execute_agent(
        state,
        "demand_estimator",
        "demand_result",
        run_demand_estimator,
        store_id=state["store_id"],
        product_id=state["product_id"],
        date=state["date"]
    )



def knowledge_agent_node(state: InvestigationState):

    question = state["question"]

    if state.get("route") == "hybrid":

        question = (
            "Explain the scientific implications of stockouts "
            "and censored demand for retail demand forecasting. "
            "Focus on forecasting bias, demand reconstruction "
            "and inventory management. "
            "Do not calculate product-specific lost demand."
        )

    return execute_agent(
        state,
        "knowledge_agent",
        "knowledge_result",
        run_knowledge_agent,
        question=question,
        top_k=state.get("top_k", 3)
    )

def quality_controller_node(state: InvestigationState):

    results = [
        state[key]
        for key in (
            "data_result",
            "demand_result",
            "knowledge_result"
        )
        if key in state
    ]

    return execute_agent(
        state,
        "quality_controller",
        "quality_result",
        run_quality_controller,
        agent_results=results
    )


def final_response_node(state: InvestigationState):

    quality = state.get("quality_result", {})

    results = [
        state[key]
        for key in (
            "data_result",
            "demand_result",
            "knowledge_result"
        )
        if key in state
    ]

    sections = []

    if quality.get("approved") is not True:

        sections.append(
            "The generated analysis could not be approved "
            "by the Quality Controller."
        )

        sections.extend(
            quality.get("issues", [])
        )

    else:

        for result in results:

            sections.append(
                f"## {result['agent'].replace('_', ' ').title()}"
            )

            sections.append(
                result.get("analysis", "")
            )

            if result.get("agent") == "knowledge_agent":
                if result.get("sources"):
                    sections.append("### Retrieved sources")

                    for source in result["sources"]:
                        sections.append(
                            f"[{source['citation_id']}] "
                            f"{source['source']}, "
                            f"page {source['page']}"
                        )

    total_tokens = sum(
        (result.get("token_usage") or {}).get(
            "total_tokens", 0
        )
        for result in [*results, quality]
    )

    return {
        "final_answer": "\n\n".join(sections),
        "total_tokens": total_tokens,
        "execution_trace": [
            *state.get("execution_trace", []),
            "final_response"
        ]
    }
