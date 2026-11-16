
from langgraph.graph import StateGraph, START, END

from src.workflows.state import InvestigationState

from src.workflows.nodes import (
    data_analyst_node,
    demand_estimator_node,
    knowledge_agent_node,
    quality_controller_node,
    final_response_node
)


def build_static_workflow():

    graph = StateGraph(InvestigationState)

    # Register nodes
    graph.add_node("data_analyst", data_analyst_node)

    graph.add_node(
        "demand_estimator", demand_estimator_node
    )

    graph.add_node(
        "knowledge_agent", knowledge_agent_node
    )

    graph.add_node(
        "quality_controller", quality_controller_node
    )

    graph.add_node(
        "final_response", final_response_node
    )

    # Define the fixed execution sequence
    graph.add_edge(START, "data_analyst")

    graph.add_edge(
        "data_analyst", "demand_estimator"
    )

    graph.add_edge(
        "demand_estimator", "knowledge_agent"
    )

    graph.add_edge(
        "knowledge_agent", "quality_controller"
    )

    graph.add_edge(
        "quality_controller", "final_response"
    )

    graph.add_edge("final_response", END)

    return graph.compile()
