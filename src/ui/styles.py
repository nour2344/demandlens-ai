import streamlit as st


def apply_styles():
    st.markdown('''<style>
    .block-container {max-width: 1440px; padding-top: 3.5rem; padding-bottom: 2rem;}
    [data-testid="stSidebar"] {border-right: 1px solid #e5e9e6;}
    [data-testid="stMetricValue"] {font-size: 1.9rem; font-weight: 600; letter-spacing: -0.045em;}
    h1,h2,h3 {letter-spacing: -0.035em;}
    [data-testid="stMetricLabel"] {color:#586861;}
    .dl-kicker {font-size:11px; letter-spacing:.13em; color:#66776e; font-weight:600; text-transform:uppercase;}
    .dl-intro {color:#64736c; font-size:14px; margin:0 0 12px;}
    </style>''', unsafe_allow_html=True)
