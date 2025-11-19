import streamlit as st
from storage import load_bets, save_bets
from fanduel_theme import inject_fanduel_theme
from components.bet_form import bet_form
from components.bet_cards import render_bet_card
from components.dashboard import dashboard_page
from components.ocr_importer import ocr_importer

# ------------------------------------------------------------
# STREAMLIT CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="FanDuel Betting Tracker",
    layout="wide",
    page_icon="💸",
)

inject_fanduel_theme()

# ------------------------------------------------------------
# UNIT SIZE (FOR KELLY + EV)
# ------------------------------------------------------------
if "unit_size" not in st.session_state:
    st.session_state.unit_size = 10.0

# ------------------------------------------------------------
# NAVIGATION
# ------------------------------------------------------------
menu = ["Dashboard", "Add Bet", "Bet History", "OCR Importer", "Settings"]
choice = st.sidebar.radio("📍 Navigate", menu)

bets = load_bets()

# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------
if choice == "Dashboard":
    dashboard_page(bets, st.session_state.unit_size)

# ------------------------------------------------------------
# ADD BET
# ------------------------------------------------------------
elif choice == "Add Bet":
    bet_form(bets)

# ------------------------------------------------------------
# BET HISTORY
# ------------------------------------------------------------
elif choice == "Bet History":
    st.header("📜 Bet History")

    if len(bets) == 0:
        st.info("No bets added yet.")
    else:
        for idx, bet in enumerate(bets):
            render_bet_card(bet, idx)

# ------------------------------------------------------------
# OCR IMPORTER
# ------------------------------------------------------------
elif choice == "OCR Importer":
    st.header("🧾 OCR Importer")
    ocr_importer()

# ------------------------------------------------------------
# SETTINGS
# ------------------------------------------------------------
elif choice == "Settings":
    st.header("⚙️ Settings")

    st.session_state.unit_size = st.number_input(
        "Unit size ($)",
        value=st.session_state.unit_size,
        min_value=1.0,
        step=1.0,
    )

    st.success("Settings updated!")
