
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


ROOT_DIR = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT_DIR / "evaluation" / "results"


AGENT_NAMES = {
    "router": "Intelligent Router",
    "data_analyst": "Data Analyst",
    "demand_estimator": "Demand Estimator",
    "knowledge_agent": "Knowledge Agent",
    "quality_controller": "Quality Controller",
    "final_response": "Final Response",
    "clarification": "Clarification"
}


def render_metrics(result):

    data = result.get("data_result", {}).get("data", {})
    demand = result.get("demand_result", {}).get("data", {})

    recorded = data.get("recorded_sales")
    lost = demand.get("estimated_lost_demand")
    total = demand.get("estimated_total_demand")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Recorded sales",
        f"{recorded:.4f}" if recorded is not None else "N/A"
    )

    col2.metric(
        "Estimated lost demand",
        f"{lost:.4f}" if lost is not None else "N/A"
    )

    col3.metric(
        "Adjusted demand",
        f"{total:.4f}" if total is not None else "N/A"
    )

    col4.metric(
        "Stockout hours",
        data.get("total_stockout_hours", "N/A")
    )

    st.caption(
        "Sales values are normalized. Adjusted demand "
        "includes estimated losses within the daytime scope only."
    )


def render_stockout_chart(result):

    data = result.get("data_result", {}).get("data", {})

    if data.get("status") != "success":
        return

    stockout_hours = data.get("stockout_hours", [])

    colors = [
        "#DC2626" if hour in stockout_hours
        else "#0D9488"
        for hour in range(24)
    ]

    labels = [
        "Stockout" if hour in stockout_hours
        else "Available"
        for hour in range(24)
    ]

    fig = go.Figure(go.Bar(
        x=[f"{hour:02d}:00" for hour in range(24)],
        y=[1] * 24,
        marker_color=colors,
        text=labels,
        hovertemplate="%{x}: %{text}<extra></extra>"
    ))

    fig.update_layout(
        title="24-hour stock availability",
        template="plotly_white",
        height=220,
        showlegend=False,
        bargap=0.12,
        yaxis=dict(visible=False),
        margin=dict(l=10, r=10, t=55, b=15)
    )

    st.plotly_chart(fig, use_container_width=True)
    st.caption("Teal: available | Red: stockout")


def render_demand_chart(result):

    demand = result.get("demand_result", {}).get("data", {})

    if demand.get("status") == "insufficient_evidence":

        st.warning(
            "Demand estimation unavailable: insufficient "
            "comparable historical observations."
        )

        st.write(
            "Unsupported hours:",
            demand.get("unsupported_hours", [])
        )

        return

    if demand.get("status") != "success":
        return

    estimates = demand.get("hourly_estimates", [])

    if not estimates:
        return

    df = pd.DataFrame(estimates)

    df["hour_label"] = df["hour"].apply(
        lambda hour: f"{hour:02d}:00"
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["hour_label"],
        y=df["actual_sales"],
        name="Observed sales",
        marker_color="#94A3B8"
    ))

    fig.add_trace(go.Bar(
        x=df["hour_label"],
        y=df["expected_sales"],
        name="Expected sales",
        marker_color="#0D9488"
    ))

    fig.update_layout(
        title="Hourly demand reconstruction",
        template="plotly_white",
        barmode="group",
        height=370,
        xaxis_title="Stockout hour",
        yaxis_title="Normalized sales",
        legend=dict(orientation="h"),
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        df.drop(columns=["hour_label"]),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Expected sales are statistical estimates, "
        "not measurements of true customer demand."
    )


def render_execution_trace(result):

    trace = result.get("execution_trace", [])

    if not trace:
        return

    agent_keys = {
        "data_analyst": "data_result",
        "demand_estimator": "demand_result",
        "knowledge_agent": "knowledge_result",
        "quality_controller": "quality_result"
    }

    st.subheader("Execution trace")

    for index, node in enumerate(trace, start=1):

        name = AGENT_NAMES.get(node, node)
        key = agent_keys.get(node)

        status = (
            result.get(key, {}).get("status", "executed")
            if key else "executed"
        )

        st.markdown(f"**{index:02d} — {name}**")
        st.caption(f"Status: {status}")

        if index < len(trace):
            st.markdown("↓")

    if result.get("router_result"):
        with st.expander("Routing decision"):
            st.json(result["router_result"])


def render_quality_control(result):

    quality = result.get("quality_result", {})

    if not quality:
        st.info("Quality review was not required.")
        return

    if quality.get("approved") is True:
        st.success("Quality review passed.")
    else:
        st.error("Analysis not approved by Quality Controller.")

    st.write("Verification type:",
             quality.get("validation_type", "N/A"))

    st.write("Attempts:", quality.get("attempts", "N/A"))

    for issue in quality.get("issues", []):
        st.warning(issue)

    if quality.get("recommendation"):
        st.write(quality["recommendation"])

    st.caption(
        "Quality approval reduces risk but does not "
        "guarantee factual correctness."
    )


def render_sources(result):

    if result.get("quality_result", {}).get("approved") is not True:
        st.info("Scientific output was not approved.")
        return

    sources = result.get("knowledge_result", {}).get("sources", [])

    if not sources:
        st.info("No scientific passages retrieved.")
        return

    for source in sources:

        label = (
            f"[{source['citation_id']}] "
            f"{source['source']} — Page {source['page']}"
        )

        with st.expander(label):

            st.write(source["text"])

            st.caption(
                f"Cosine distance: {source['distance']}"
            )


def load_report(filename):

    path = RESULTS_DIR / filename

    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as file:
        return json.load(file)


def render_evaluation():

    st.header("System evaluation")

    demand = load_report("demand_metrics.json")
    workflow = load_report("workflow_evaluation.json")
    context = load_report("context_evaluation.json")

    if demand:

        st.subheader("Demand reconstruction experiment")

        model = demand.get("demand_estimator", {})
        baseline = demand.get("zero_demand_baseline", {})

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Evaluation cases",
            demand["evaluation_cases"]
        )

        col2.metric(
            "Estimation coverage",
            f"{demand['coverage_percentage']:.1f}%"
        )

        if model and baseline and baseline["mae"] > 0:

            improvement = (
                1 - model["mae"] / baseline["mae"]
            ) * 100

            col3.metric(
                "MAE improvement",
                f"{improvement:.2f}%"
            )

            metrics = pd.DataFrame({
                "DemandLens AI": model,
                "Zero-demand baseline": baseline
            })

            st.dataframe(metrics, use_container_width=True)

            fig = go.Figure()

            for name, values, color in [
                ("DemandLens AI", model, "#0D9488"),
                ("Baseline", baseline, "#94A3B8")
            ]:

                fig.add_trace(go.Bar(
                    x=["MAE", "RMSE"],
                    y=[values["mae"], values["rmse"]],
                    name=name,
                    marker_color=color
                ))

            fig.update_layout(
                barmode="group",
                template="plotly_white",
                height=320,
                title="Estimation error comparison"
            )

            st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Synthetic stockout experiment. Accuracy metrics "
            "apply to successfully estimated cases."
        )

    if workflow:

        st.divider()
        st.subheader("Multi-agent workflow evaluation")

        summary = workflow["summary"]

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Routing accuracy",
            f"{summary['routing_accuracy']:.1%}"
        )

        col2.metric(
            "End-to-end pass rate",
            f"{summary['overall_pass_rate']:.1%}"
        )

        col3.metric(
            "Average latency",
            f"{summary['average_latency_seconds']:.2f}s"
        )

        df = pd.DataFrame(workflow["results"])

        columns = [
            "case", "actual_route",
            "actual_outcome", "passed",
            "tokens", "latency_seconds"
        ]

        st.dataframe(
            df[columns],
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Results from predefined evaluation scenarios, "
            "not general production accuracy."
        )

    if context:

        st.divider()
        st.subheader("RAG context experiment")

        df = pd.DataFrame(context["configurations"])

        columns = [
            "top_k", "context_characters",
            "total_tokens", "latency_seconds",
            "quality_approved"
        ]

        st.dataframe(
            df[columns],
            use_container_width=True,
            hide_index=True
        )

        fig = go.Figure(go.Bar(
            x=[f"k={k}" for k in df["top_k"]],
            y=df["total_tokens"],
            marker_color=["#0D9488", "#64748B"]
        ))

        fig.update_layout(
            title="Generation token consumption",
            template="plotly_white",
            height=300
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "One execution per context configuration. "
            "Verification tokens are recorded separately."
        )

    if not any([demand, workflow, context]):
        st.info("No saved evaluation reports found.")
