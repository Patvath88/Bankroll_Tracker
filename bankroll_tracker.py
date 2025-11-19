import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import json
import requests

# ============================================================
# DATA INITIALIZATION
# ============================================================

DATA_FILE = "bets.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Date", "Sport", "Bet Type", "Player/Team", "Odds",
        "Stake", "Result", "Profit", "Imported"
    ])
    df.to_csv(DATA_FILE, index=False)

st.set_page_config(page_title="Bankroll Tracker", layout="wide")

st.title("🔥 Advanced Sports Betting Bankroll Tracker + FanDuel Importer")


# ============================================================
# SIDEBAR BANKROLL SUMMARY
# ============================================================

st.sidebar.header("📊 Bankroll Summary")

total_profit = df["Profit"].sum()
starting_bankroll = st.sidebar.number_input("Starting Bankroll ($)", value=1000)

bankroll = starting_bankroll + total_profit

wins = df[df["Profit"] > 0].shape[0]
losses = df[df["Profit"] < 0].shape[0]
win_rate = (wins / max(1, wins + losses)) * 100

st.sidebar.metric("Current Bankroll", f"${bankroll:.2f}")
st.sidebar.metric("Total Profit", f"${total_profit:.2f}")
st.sidebar.metric("Win Rate", f"{win_rate:.1f}%")


# ============================================================
# UNIT SIZING TOOLS
# ============================================================

st.subheader("📐 Unit Sizing Tools")

colU1, colU2, colU3 = st.columns(3)

with colU1:
    kelly_edge = st.number_input("Estimated Edge (%)", value=5.0)
with colU2:
    kelly_win_prob = st.number_input("Win Probability (%)", value=55.0)
with colU3:
    fixed_unit = st.number_input("Fixed Unit Size ($)", value=25.0)


def kelly_fraction(win_prob, odds):
    """Kelly criterion fraction calculation."""
    decimal_odds = (odds / 100) + 1 if odds > 0 else (100 / abs(odds)) + 1
    p = win_prob / 100
    b = decimal_odds - 1
    return (b * p - (1 - p)) / b


def recommend_stakes(odds):
    """Returns (kelly stake, risk %, fixed unit)."""
    k_fraction = max(0, kelly_fraction(kelly_win_prob, odds))
    kelly_stake = bankroll * k_fraction
    risk_percent_stake = bankroll * (kelly_edge / 100)
    return kelly_stake, risk_percent_stake, fixed_unit


# ============================================================
# MANUAL BET ENTRY
# ============================================================

st.subheader("➕ Add Manual Bet")

with st.form("manual_bet"):
    c1, c2, c3 = st.columns(3)

    with c1:
        date = st.date_input("Date", datetime.today())
        sport = st.text_input("Sport")
        bet_type = st.text_input("Bet Type")

    with c2:
        player_team = st.text_input("Player/Team")
        odds = st.number_input("Odds (American)", step=1)
        stake = st.number_input("Stake ($)", step=1.0)

    with c3:
        result = st.selectbox("Result", ["Pending", "Win", "Loss", "Push"])

    submitted_manual = st.form_submit_button("Add Bet")

if submitted_manual:
    if result == "Win":
        profit = stake * (odds / 100) if odds > 0 else stake / (abs(odds) / 100)
    elif result == "Loss":
        profit = -stake
    else:
        profit = 0

    new_row = {
        "Date": str(date),
        "Sport": sport,
        "Bet Type": bet_type,
        "Player/Team": player_team,
        "Odds": odds,
        "Stake": stake,
        "Result": result,
        "Profit": profit,
        "Imported": False
    }

    df = df.append(new_row, ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("Manual Bet Added!")


# ============================================================
# NEW BETSLIP UPLOAD USING EASYOCR (works on Streamlit Cloud)
# ============================================================

import easyocr
from PIL import Image
import numpy as np

st.subheader("📸 Upload Bet Slip (Image)")

uploaded_betslip = st.file_uploader(
    "Upload your bet slip screenshot (JPG, PNG)", 
    type=["jpg", "jpeg", "png"]
)

# Load EasyOCR reader (cached so it doesn't reload every time)
@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()


def extract_text_easyocr(image):
    """
    Use EasyOCR to extract all text from a bet slip image.
    """
    img_array = np.array(image)
    results = reader.readtext(img_array, detail=0)
    return "\n".join(results)


def parse_betslip_text(text):
    """
    Extracts basic betting details from OCR output.
    """
    lines = text.split("\n")
    result = {
        "Player/Team": "",
        "Odds": 0,
        "Stake": 0,
        "Bet Type": "Imported"
    }

    for line in lines:
        line_clean = line.strip()

        # Find American odds
        if "+" in line_clean or "-" in line_clean:
            for token in line_clean.split():
                try:
                    if token.startswith("+") or token.startswith("-"):
                        result["Odds"] = int(token)
                except:
                    pass

        # Find stake
        if "stake" in line_clean.lower() or "$" in line_clean.lower():
            tokens = line_clean.replace("$", "").split()
            for t in tokens:
                if t.replace(".", "").isdigit():
                    result["Stake"] = float(t)

        # Guess player/team as longest non-numeric line
        if len(line_clean) > len(result["Player/Team"]) and not any(char.isdigit() for char in line_clean):
            result["Player/Team"] = line_clean

    return result


if uploaded_betslip:
    st.info("Extracting text from bet slip…")

    image = Image.open(uploaded_betslip)

    extracted_text = extract_text_easyocr(image)

    parsed = parse_betslip_text(extracted_text)

    st.subheader("📝 Parsed Bet Details (Edit if needed)")
    with st.form("parsed_bet_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            date = st.date_input("Date", datetime.today())
            player_team = st.text_input("Player/Team", value=parsed["Player/Team"])
        with col2:
            odds = st.number_input("Odds", value=parsed["Odds"])
            stake = st.number_input("Stake ($)", value=parsed["Stake"])
        with col3:
            bet_type = st.text_input("Bet Type", value="Imported")
            result = st.selectbox("Result", ["Pending", "Win", "Loss", "Push"])

        submitted_import = st.form_submit_button("Add Bet to Tracker")

    if submitted_import:
        if result == "Win":
            profit = stake * (odds / 100) if odds > 0 else stake / (abs(odds) / 100)
        elif result == "Loss":
            profit = -stake
        else:
            profit = 0

        new_row = {
            "Date": str(date),
            "Sport": "Auto",
            "Bet Type": bet_type,
            "Player/Team": player_team,
            "Odds": odds,
            "Stake": stake,
            "Result": result,
            "Profit": profit,
            "Imported": True
        }

        df.loc[len(df)] = new_row
        df.to_csv(DATA_FILE, index=False)

        st.success("Bet Slip Imported Successfully!")



# ============================================================
# BET HISTORY TABLE
# ============================================================

st.subheader("📜 Bet History")
st.dataframe(df)


# ============================================================
# PROFIT GRAPH
# ============================================================

if not df.empty:
    df_graph = df.copy()
    df_graph["Date"] = pd.to_datetime(df_graph["Date"])
    df_graph["Cumulative Profit"] = df_graph["Profit"].cumsum()

    st.subheader("📈 Profit Over Time")
    st.line_chart(df_graph[["Date", "Cumulative Profit"]].set_index("Date"))
