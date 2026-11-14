
from datetime import date

from langgraph.graph import StateGraph, START, END

from src.workflows.state import InvestigationState
from src.agents.router import classify_request

from src.workflows.nodes import (
    data_analyst_node,
    demand_estimator_node,
    knowledge_agent_node,
    quality_controller_node,
    final_response_node
)


def router_node(state):

    try:
        decision = classify_request(
            state.get("question", "")
        )

        route = decision["route"]

        clarification = (
            "Please clarify your retail demand question."
        )

        if route in {"data", "estimate", "hybrid"}:

            missing = [
                field
                for field in ("store_id", "product_id", "date")
                if state.get(field) is None
                or state.get(field) == ""
            ]

            if missing:
                route = "clarify"
                clarification = (
                    "Please provide: "
                    + ", ".join(missing)
                )

            else:
                try:
                    date.fromisoformat(state["date"])
                except (ValueError, TypeError):
                    route = "clarify"
                    clarification = (
                        "Please provide a date in YYYY-MM-DD format."
                    )

    except Exception as error:

        route = "clarify"

        decision = {
            "error_type": type(error).__name__
        }

        clarification = (
            "The request could not be classified. "
            "Please rephrase your question or try again."
        )

    return {
        "route": route,
        "router_result": decision,
        "clarification": clarification,
        "execution_trace": [
            *state.get("execution_trace", []),
            "router"
        ]
    }


def route_after_router(state):

    route = state["route"]

    if route == "knowledge":
        return "knowledge_agent"

    if route == "clarify":
        return "clarification"

    return "data_analyst"


def route_after_data(state):

    result = state.get("data_result", {})
    data = result.get("data", {})

    if result.get("status") != "success":
        return "quality_controller"

    needs_estimate = state["route"] in {
        "estimate", "hybrid"
    }

    daytime_stockout = (
        data.get("daytime_stockout_hours", 0) > 0
    )

    if needs_estimate and daytime_stockout:
        return "demand_estimator"

    if state["route"] == "hybrid":
        return "knowledge_agent"

    return "quality_controller"


def route_after_demand(state):

    if state["route"] == "hybrid":
        return "knowledge_agent"

    return "quality_controller"


def clarification_node(state):

    return {
        "final_answer": state["clarification"],
        "total_tokens": (
            state.get("router_result", {})
            .get("token_usage") or {}
        ).get("total_tokens", 0),
        "execution_trace": [
            *state.get("execution_trace", []),
            "clarification"
        ]
    }


def dynamic_final_response_node(state):

    result = final_response_node(state)

    router_usage = (
        state.get("router_result", {})
        .get("token_usage") or {}
    )

    result["total_tokens"] += (
        router_usage.get("total_tokens", 0)
        + state.get("retry_tokens", 0)
    )

    return result


def build_dynamic_workflow():

    graph = StateGraph(InvestigationState)

    # Register nodes
    graph.add_node("router", router_node)
    graph.add_node("data_analyst", data_analyst_node)
    graph.add_node("demand_estimator", demand_estimator_node)
    graph.add_node("knowledge_agent", knowledge_agent_node)
    graph.add_node("quality_controller", quality_controller_node)
    graph.add_node("clarification", clarification_node)
    graph.add_node("final_response", dynamic_final_response_node)

    graph.add_edge(START, "router")

    # Dynamic routing
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "data_analyst": "data_analyst",
            "knowledge_agent": "knowledge_agent",
            "clarification": "clarification"
        }
    )

    graph.add_conditional_edges(
        "data_analyst",
        route_after_data,
        {
            "demand_estimator": "demand_estimator",
            "knowledge_agent": "knowledge_agent",
            "quality_controller": "quality_controller"
        }
    )

    graph.add_conditional_edges(
        "demand_estimator",
        route_after_demand,
        {
            "knowledge_agent": "knowledge_agent",
            "quality_controller": "quality_controller"
        }
    )

    graph.add_edge(
        "knowledge_agent", "quality_controller"
    )

    graph.add_edge(
        "quality_controller", "final_response"
    )

    graph.add_edge("clarification", END)
    graph.add_edge("final_response", END)

    return graph.compile()
