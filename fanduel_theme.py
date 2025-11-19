import streamlit as st

# --------------------------------------------------------
# FanDuel Color Palette
# --------------------------------------------------------

FD_BLUE = "#0B6EFD"         # Main FD Blue
FD_DARK_BLUE = "#084298"    # Darker Blue
FD_LIGHT_BLUE = "#E9F2FF"   # Very Light Blue
FD_GREEN = "#28C76F"        # Win color
FD_RED = "#EA5455"          # Loss color
FD_GRAY = "#6C757D"         # Secondary text
FD_BG = "#F8F9FA"           # Background
FD_CARD_BG = "#FFFFFF"      # Card background

# --------------------------------------------------------
# Inject Global FanDuel CSS Theme
# --------------------------------------------------------

def inject_fanduel_theme():
    st.markdown(
        f"""
        <style>

        /* -------------------------------------- */
        /* GLOBAL PAGE BACKGROUND */
        /* -------------------------------------- */
        .main {{
            background-color: {FD_BG};
            padding: 0;
        }}

        /* -------------------------------------- */
        /* HEADERS */
        /* -------------------------------------- */
        h1, h2, h3, h4, h5 {{
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 700;
        }}

        /* -------------------------------------- */
        /* BET CARDS */
        /* -------------------------------------- */
        .bet-card {{
            background: {FD_CARD_BG};
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 18px;
            box-shadow: 0px 4px 14px rgba(0,0,0,0.08);
            border: 1px solid #E1E4E7;
        }}

        .bet-header {{
            font-size: 20px;
            font-weight: 700;
            color: {FD_DARK_BLUE};
            margin-bottom: 8px;
        }}

        .bet-subheader {{
            font-size: 14px;
            color: {FD_GRAY};
            margin-bottom: 12px;
        }}

        .bet-odds {{
            font-size: 18px;
            font-weight: 600;
            color: {FD_DARK_BLUE};
        }}

        .bet-profit-win {{
            color: {FD_GREEN};
            font-weight: 700;
        }}

        .bet-profit-loss {{
            color: {FD_RED};
            font-weight: 700;
        }}

        /* -------------------------------------- */
        /* PARLAY LEG TABLE */
        /* -------------------------------------- */
        .leg-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 8px;
            margin-bottom: 12px;
        }}

        .leg-table th {{
            text-align: left;
            padding: 6px;
            background: {FD_LIGHT_BLUE};
            color: {FD_DARK_BLUE};
            font-weight: 700;
            border-bottom: 1px solid #d9e1ea;
        }}

        .leg-table td {{
            padding: 6px;
            font-size: 14px;
            border-bottom: 1px solid #EEEEEE;
        }}

        /* -------------------------------------- */
        /* BUTTONS */
        /* -------------------------------------- */
        .stButton>button {{
            background: {FD_BLUE};
            color: white;
            border-radius: 10px;
            border: none;
            padding: 12px 20px;
            font-size: 16px;
            font-weight: 600;
        }}

        .stButton>button:hover {{
            background: {FD_DARK_BLUE};
            color: white;
        }}

        /* DELETE BUTTON */
        .delete-button button {{
            background: {FD_RED} !important;
        }}
        .delete-button button:hover {{
            background: #c83536 !important;
        }}

        /* EDIT BUTTON */
        .edit-button button {{
            background: {FD_GRAY} !important;
        }}
        .edit-button button:hover {{
            background: #555 !important;
        }}

        /* -------------------------------------- */
        /* COLLAPSIBLE AREA */
        /* -------------------------------------- */
        summary {{
            font-weight: 600;
            cursor: pointer;
            color: {FD_BLUE};
            margin-bottom: 8px;
        }}
        summary:hover {{
            color: {FD_DARK_BLUE};
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )
