
from datetime import date
from time import perf_counter

import streamlit as st

from src.workflows.static_workflow import build_static_workflow
from src.workflows.dynamic_workflow import build_dynamic_workflow

from src.ui.styles import apply_styles, render_header

from src.ui.components import (
    render_metrics,
    render_stockout_chart,
    render_demand_chart,
    render_execution_trace,
    render_quality_control,
    render_sources,
    render_evaluation
)


st.set_page_config(
    page_title="DemandLens AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_styles()


DEMO_CASES = {
    "Full investigation": {
        "question": (
            "Estimate lost demand for this product "
            "and explain the scientific forecasting implications."
        ),
        "store_id": 1,
        "product_id": 793
    },
    "Stockout investigation": {
        "question": "Did this product experience a stockout?",
        "store_id": 1,
        "product_id": 793
    },
    "Demand estimation": {
        "question": "Estimate hidden demand for this product.",
        "store_id": 1,
        "product_id": 793
    },
    "Scientific question": {
        "question": "What is censored demand in retail?",
        "store_id": 1,
        "product_id": 793
    },
    "Insufficient evidence": {
        "question": "Estimate lost demand for this product.",
        "store_id": 0,
        "product_id": 72
    },
    "Missing information": {
        "question": "Estimate lost demand for my product.",
        "store_id": 1,
        "product_id": 793
    }
}


with st.sidebar:

    st.title("DemandLens AI")
    st.caption("Retail Intelligence Workspace")

    page = st.radio(
        "Navigation",
        ["Investigation", "System evaluation"]
    )

    st.divider()

    if page == "Investigation":

        workflow_mode = st.radio(
            "Orchestration mode",
            ["Dynamic", "Static"]
        )

        scenario = st.selectbox(
            "Demo scenario",
            list(DEMO_CASES.keys())
        )

        demo = DEMO_CASES[scenario]

        include_identifiers = st.checkbox(
            "Include retail identifiers",
            value=scenario != "Missing information",
            key=f"identifiers_{scenario}"
        )

        if workflow_mode == "Static":
            include_identifiers = True

        store_id = st.number_input(
            "Store ID",
            min_value=0,
            value=demo["store_id"],
            step=1,
            key=f"store_{scenario}"
        )

        product_id = st.number_input(
            "Product ID",
            min_value=0,
            value=demo["product_id"],
            step=1,
            key=f"product_{scenario}"
        )

        investigation_date = st.date_input(
            "Investigation date",
            value=date(2024, 6, 25),
            min_value=date(2024, 3, 28),
            max_value=date(2024, 6, 25)
        )

        top_k = st.slider(
            "RAG retrieval depth",
            min_value=1,
            max_value=8,
            value=3
        )

    st.divider()

    st.caption("TECHNOLOGY STACK")
    st.markdown("""
    - GPT-OSS-20B via Groq
    - LangGraph
    - ChromaDB
    - Streamlit & Plotly
    """)

    st.caption("DemandLens AI · Research prototype")


render_header()


if page == "System evaluation":

    render_evaluation()

else:

    st.subheader("Investigation workspace")

    question = st.text_area(
        "What would you like to investigate?",
        value=demo["question"],
        height=100,
        key=f"question_{scenario}"
    )

    if st.button(
        "Run investigation",
        type="primary",
        use_container_width=True
    ):

        if not question.strip():

            st.warning("Please enter an investigation question.")

        else:

            initial_state = {
                "question": question,
                "top_k": top_k,
                "execution_trace": [],
                "retry_count": 0,
                "retry_tokens": 0
            }

            if include_identifiers:

                initial_state.update({
                    "store_id": int(store_id),
                    "product_id": int(product_id),
                    "date": investigation_date.isoformat()
                })

            st.session_state.pop("investigation_result", None)

            with st.spinner("AI agents are investigating..."):

                start = perf_counter()

                try:

                    if workflow_mode == "Static":
                        workflow = build_static_workflow()
                    else:
                        workflow = build_dynamic_workflow()

                    result = workflow.invoke(initial_state)

                    st.session_state["investigation_result"] = {
                        "result": result,
                        "latency": round(
                            perf_counter() - start, 3
                        ),
                        "mode": workflow_mode,
                        "question": question
                    }

                except Exception as error:

                    st.error(
                        f"Investigation failed: "
                        f"{type(error).__name__}"
                    )

    if "investigation_result" in st.session_state:

        saved = st.session_state["investigation_result"]

        result = saved["result"]
        quality = result.get("quality_result", {})

        st.divider()

        st.caption(
            f"Last completed investigation · {saved['mode']}"
        )

        st.write(saved["question"])

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Workflow",
            saved["mode"]
        )

        col2.metric(
            "Reported tokens",
            result.get("total_tokens", 0)
        )

        col3.metric(
            "Execution time",
            f"{saved['latency']:.2f}s"
        )

        tab1, tab2, tab3, tab4 = st.tabs([
            "Investigation results",
            "Agent orchestration",
            "Scientific evidence",
            "Quality control"
        ])

        with tab1:

            if quality.get("approved") is True:

                if result.get("data_result"):
                    render_metrics(result)
                    render_stockout_chart(result)
                    render_demand_chart(result)

                st.subheader("Investigation report")
                st.markdown(result.get("final_answer", ""))

            elif "clarification" in result.get(
                "execution_trace", []
            ):

                st.info(result.get("final_answer", ""))

            else:

                st.warning(
                    "The investigation could not be approved."
                )

                st.markdown(result.get("final_answer", ""))

        with tab2:
            render_execution_trace(result)

        with tab3:
            render_sources(result)

        with tab4:
            render_quality_control(result)
