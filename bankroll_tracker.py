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
# FAN DUEL COOKIE IMPORTER (ACTIVE + SETTLED)
# ============================================================

st.subheader("🔁 Import FanDuel Bets (via Cookies)")

uploaded_cookies = st.file_uploader("Upload fanduel_cookies.json", type=["json"])


def load_cookies(uploaded):
    try:
        cookies_raw = json.load(uploaded)
        return {c["name"]: c["value"] for c in cookies_raw}
    except Exception as e:
        st.error(f"Error parsing cookies: {e}")
        return None


def fetch_fanduel_bets(cookies):
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    # Set cookies
    session.cookies.update(cookies)

    # ============= Active Bets =============
    active_url = "https://sportsbook.fanduel.com/api/bets/active"
    settled_url = "https://sportsbook.fanduel.com/api/bets/settled"

    all_bets = []

    for url, label in [(active_url, "Active"), (settled_url, "Settled")]:
        try:
            r = session.get(url)
            if r.status_code != 200:
                continue

            data = r.json().get("bets", [])

            for b in data:
                desc = b.get("description", "N/A")
                stake = float(b.get("stake", 0))
                odds = int(b.get("oddsAmerican", 0))
                result = (
                    "Win" if b.get("result") == "WON" else
                    "Loss" if b.get("result") == "LOST" else
                    "Pending"
                )

                if result == "Win":
                    profit = stake * (odds / 100) if odds > 0 else stake / (abs(odds) / 100)
                elif result == "Loss":
                    profit = -stake
                else:
                    profit = 0

                all_bets.append({
                    "Date": datetime.today().strftime("%Y-%m-%d"),
                    "Sport": "Auto",
                    "Bet Type": label,
                    "Player/Team": desc,
                    "Odds": odds,
                    "Stake": stake,
                    "Result": result,
                    "Profit": profit,
                    "Imported": True
                })

        except Exception as e:
            st.warning(f"Error fetching {label} bets: {e}")

    return all_bets


if uploaded_cookies:
    cookies = load_cookies(uploaded_cookies)

    if cookies:
        st.info("Fetching FanDuel bets...")

        bets = fetch_fanduel_bets(cookies)

        if len(bets) > 0:
            imported_df = pd.DataFrame(bets)

            df = pd.concat([df, imported_df], ignore_index=True)

            df.drop_duplicates(subset=["Player/Team", "Stake", "Odds"], keep="first", inplace=True)

            df.to_csv(DATA_FILE, index=False)

            st.success(f"Imported {len(imported_df)} FanDuel bets!")

        else:
            st.warning("No bets found. Are your cookies still valid?")


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
