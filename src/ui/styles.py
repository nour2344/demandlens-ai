
import streamlit as st


def apply_styles():

    st.markdown("""
    <style>

    .stApp {
        background-color: #F8FAFC;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }

    [data-testid="stSidebar"] {
        background-color: #E8EEF4;
    }

    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #E2E8F0;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04);
    }

    [data-testid="stMetricValue"] {
        color: #0D9488;
        font-weight: 700;
    }

    .stButton > button {
        background-color: #0D9488;
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        min-height: 44px;
    }

    .stButton > button:hover {
        background-color: #0F766E;
        color: white;
    }

    .hero {
        background: linear-gradient(
            120deg, #0F172A, #115E59
        );
        border-radius: 16px;
        padding: 32px;
        margin-bottom: 25px;
        color: white;
    }

    .hero h1 {
        color: white;
        margin: 0;
        font-size: 2.3rem;
    }

    .hero p {
        color: #CBD5E1;
        margin: 12px 0 0;
    }

    </style>
    """, unsafe_allow_html=True)


def render_header():

    st.markdown("""
    <div class="hero">
        <div style="color:#5EEAD4;
                    font-size:12px;
                    letter-spacing:3px;">
            AGENTIC RETAIL INTELLIGENCE
        </div>
        <h1>DemandLens AI</h1>
        <p>
            Uncover hidden demand.
            Investigate stockouts.
            Make evidence-driven decisions.
        </p>
    </div>
    """, unsafe_allow_html=True)
