import streamlit as st

FD_BLUE = "#0094FF"
FD_GREEN = "#00C853"
FD_RED = "#FF1744"

def inject_fanduel_theme():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: #F5F8FC;
        }}
        .fanduel-card {{
            background-color: white;
            border: 2px solid {FD_BLUE};
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 12px;
        }}
        .bet-header {{
            font-size: 20px;
            font-weight: 700;
            color: {FD_BLUE};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
