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
# PARLAY-CAPABLE BETSLIP IMPORT (EASYOCR VERSION)
# ============================================================

import easyocr
from PIL import Image
import numpy as np
import re

st.subheader("📸 Upload Bet Slip (Straight or Parlay)")

uploaded_betslip = st.file_uploader(
    "Upload your bet slip (JPG/PNG)", 
    type=["jpg", "jpeg", "png"]
)

@st.cache_resource
def load_reader():
    return easyocr.Reader(['en'], gpu=False)

reader = load_reader()

def extract_text_easyocr(image):
    img_array = np.array(image)
    results = reader.readtext(img_array, detail=0)
    return "\n".join(results)

def parse_betslip_parlay(text):
    """
    Detect whether slip is a parlay or straight.
    Extract legs automatically.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # ------ Detect Parlay keywords ------
    is_parlay = any([
        "parlay" in t.lower() for t in lines
    ])

    result = {
        "Bet Type": "Parlay" if is_parlay else "Straight",
        "Legs": [],
        "Odds": 0,
        "Stake": 0,
        "To Win": 0,
        "Payout": 0,
        "Player/Team": ""
    }

    # ------ Grab stake ------
    for line in lines:
        if "stake" in line.lower() or "$" in line.lower():
            tokens = line.replace("$", "").split()
            for t in tokens:
                if t.replace(".", "").isdigit():
                    result["Stake"] = float(t)

    # ------ Grab overall odds ------
    for line in lines:
        match = re.search(r'(\+|\-)\d{3,4}', line)
        if match:
            result["Odds"] = int(match.group(0))
            break

    # ------ Grab payout fields ------
    for line in lines:
        if "to win" in line.lower():
            nums = re.findall(r'\d+\.\d+|\d+', line)
            if nums:
                result["To Win"] = float(nums[-1])
        if "payout" in line.lower():
            nums = re.findall(r'\d+\.\d+|\d+', line)
            if nums:
                result["Payout"] = float(nums[-1])

    # ------ Extract parlay legs ------
    leg_candidates = []

    for line in lines:
        # ignore money lines
        if any(k in line.lower() for k in ["stake", "odds", "payout", "win"]):
            continue
        # ignore empty digit lines
        if line.replace(".", "").isdigit():
            continue
        # treat anything with no $ and no long digits as potential leg text
        if not any(c.isdigit() for c in line) or "/" in line:
            if len(line) > 2:
                leg_candidates.append(line)

    # If parlay: treat all candidate lines as legs
    if is_parlay:
        result["Legs"] = [{"Leg": i+1, "Description": line} for i, line in enumerate(leg_candidates)]
        # Combine legs for CSV-friendly field
        result["Player/Team"] = "PARLAY - " + " | ".join(line for line in leg_candidates)
    else:
        # Straight bet: best guess is longest line
        result["Player/Team"] = max(leg_candidates, key=len) if leg_candidates else ""

    return result


if uploaded_betslip:
    st.info("Extracting text from bet slip…")

    image = Image.open(uploaded_betslip)
    extracted_text = extract_text_easyocr(image)
    parsed = parse_betslip_parlay(extracted_text)

    st.subheader("📝 Parsed Bet Details (Edit if necessary)")

    with st.form("parsed_bet_form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            date = st.date_input("Date", datetime.today())
            bet_type = st.text_input("Bet Type", value=parsed["Bet Type"])
            player_team = st.text_input("Bet Description", value=parsed["Player/Team"])

        with col2:
            odds = st.number_input("Odds (American)", value=int(parsed["Odds"]))
            stake = st.number_input("Stake ($)", value=float(parsed["Stake"]))

        with col3:
            to_win = st.number_input("To Win ($)", value=float(parsed["To Win"]))
            payout = st.number_input("Payout ($)", value=float(parsed["Payout"]))
            result_choice = st.selectbox("Result", ["Pending", "Win", "Loss", "Push"])

        submitted_import = st.form_submit_button("Add Bet")

    if submitted_import:
        # Profit logic
        if result_choice == "Win":
            profit = to_win
        elif result_choice == "Loss":
            profit = -stake
        else:
            profit = 0

        new_row = {
            "Date": str(date),
            "Sport": "Auto",
            "Bet Type": bet_type,
            "Player/Team": player_team,  # includes all legs if parlay
            "Odds": odds,
            "Stake": stake,
            "Result": result_choice,
            "Profit": profit,
            "Imported": True
        }

        df.loc[len(df)] = new_row
        df.to_csv(DATA_FILE, index=False)

        st.success("Parlay Imported Successfully!")


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
