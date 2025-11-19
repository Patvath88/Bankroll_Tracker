import streamlit as st
from storage import load_bets, save_bets, add_bet, update_bet, delete_bet
from components.bet_form import bet_form
from components.bet_cards import render_bet_card
from components.dashboard import dashboard_page
from components.ocr_importer import ocr_importer
from fanduel_theme import inject_fanduel_theme


# -------------------------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------------------------
st.set_page_config(
    page_title="FanDuel Betting Tracker",
    layout="wide",
    page_icon="💸"
)

inject_fanduel_theme()


# -------------------------------------------------------------------
# SESSION STATE
# -------------------------------------------------------------------
if "unit_size" not in st.session_state:
    st.session_state.unit_size = 10.0  # default unit size


# -------------------------------------------------------------------
# CALLBACKS
# -------------------------------------------------------------------
def add_bet_callback(bet):
    add_bet(bet)
    st.success("Bet successfully added!")
    st.experimental_rerun()


def edit_bet_callback(index):
    st.session_state["edit_index"] = index
    st.experimental_rerun()


def delete_bet_callback(index):
    delete_bet(index)
    st.success("Bet deleted!")
    st.experimental_rerun()


# -------------------------------------------------------------------
# EDIT BET PAGE (POPUP-LIKE)
# -------------------------------------------------------------------
def edit_bet_page(index):
    st.header("✏️ Edit Bet")

    bets = load_bets()
    bet = bets[index]

    sport = st.text_input("Sport", bet["sport"])
    sportsbook = st.text_input("Sportsbook", bet["sportsbook"])
    odds = st.number_input("Odds", value=float(bet["odds"]))
    stake = st.number_input("Stake", value=float(bet["stake"]))

    notes = st.text_area("Notes", value=bet.get("notes", ""))

    if st.button("Save Changes"):
        bet["sport"] = sport
        bet["sportsbook"] = sportsbook
        bet["odds"] = odds
        bet["stake"] = stake
        bet["notes"] = notes

        update_bet(index, bet)
        st.success("Bet updated!")
        del st.session_state["edit_index"]
        st.experimental_rerun()

    if st.button("Cancel"):
        del st.session_state["edit_index"]
        st.experimental_rerun()


# -------------------------------------------------------------------
# NAVIGATION
# -------------------------------------------------------------------
menu = ["Dashboard", "Add Bet", "Bet History", "OCR Importer", "Settings"]
choice = st.sidebar.radio("📍 Navigate", menu)


# -------------------------------------------------------------------
# EDIT MODE CHECK
# -------------------------------------------------------------------
if "edit_index" in st.session_state:
    edit_bet_page(st.session_state["edit_index"])
    st.stop()


bets = load_bets()


# -------------------------------------------------------------------
# DASHBOARD PAGE
# -------------------------------------------------------------------
if choice == "Dashboard":
    dashboard_page(bets, st.session_state.unit_size)


# -------------------------------------------------------------------
# ADD BET PAGE
# -------------------------------------------------------------------
elif choice == "Add Bet":
    bet_form(add_bet_callback)


# -------------------------------------------------------------------
# BET HISTORY PAGE
# -------------------------------------------------------------------
elif choice == "Bet History":
    st.header("📜 Bet History")

    if len(bets) == 0:
        st.info("No bets added yet.")
    else:
        # Filters
        sports = sorted(set(b["sport"] for b in bets))
        types = sorted(set(b["type"] for b in bets))

        sport_filter = st.multiselect("Filter by Sport:", sports, default=sports)
        type_filter = st.multiselect("Filter by Bet Type:", types, default=types)

        for idx, b in enumerate(bets):
            if b["sport"] in sport_filter and b["type"] in type_filter:
                render_bet_card(b, idx, delete_bet_callback, edit_bet_callback)


# -------------------------------------------------------------------
# OCR IMPORTER PAGE
# -------------------------------------------------------------------
elif choice == "OCR Importer":
    st.header("🧾 OCR Bet Slip Importer")

    result = ocr_importer()
    if result:
        st.info("OCR completed — you may now manually transfer extracted data into Add Bet.")


# -------------------------------------------------------------------
# SETTINGS PAGE
# -------------------------------------------------------------------
elif choice == "Settings":
    st.header("⚙️ Settings")

    st.write("### Unit Size")
    st.session_state.unit_size = st.number_input(
        "1 Unit = $ amount",
        min_value=1.0,
        step=1.0,
        value=st.session_state.unit_size
    )

    st.success("Settings updated!")
