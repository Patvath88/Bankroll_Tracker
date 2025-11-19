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
# NEW FANDUEL IMPORTER (mobile API version)
# ============================================================

st.subheader("🔁 Import FanDuel Bets (via Cookies)")

uploaded_cookies = st.file_uploader("Upload fanduel_cookies.json", type=["json"])


def load_cookies(uploaded):
    try:
        cookies_raw = json.load(uploaded)
        cookie_dict = {c["name"]: c["value"] for c in cookies_raw}
        return cookie_dict
    except Exception as e:
        st.error(f"Error parsing cookies: {e}")
        return None


def create_mobile_session(cookies):
    """
    Creates a requests session with FanDuel mobile headers & your cookies.
    """
    s = requests.Session()

    # Standard mobile headers (required)
    s.headers.update({
        "User-Agent": "FanDuel/2500 CFNetwork/1335.0.3 Darwin/21.6.0",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    })

    # Add cookies (this DOES authenticate)
    s.cookies.update(cookies)

    return s


def fetch_mobile_bets(session):
    """
    Fetch active + recent settled bets (last ~30 days) from mobile API.
    """

    ACTIVE_URL = "https://api.fanduel.com/bets/v1/users/me/active"
    SETTLED_URL = "https://api.fanduel.com/bets/v1/users/me/settled?offset=0&count=200"

    all_results = []

    # ========================
    # ACTIVE BETS
    # ========================
    try:
        r = session.get(ACTIVE_URL)
        if r.status_code == 200:
            active_data = r.json().get("bets", [])
            for bet in active_data:
                all_results.append(process_mobile_bet(bet, "Active"))
        else:
            st.warning(f"Active request failed: HTTP {r.status_code}")
    except Exception as e:
        st.warning(f"Error fetching Active bets: {e}")

    # ========================
    # SETTLED BETS (200 max)
    # ========================
    try:
        r = session.get(SETTLED_URL)
        if r.status_code == 200:
            settled_data = r.json().get("bets", [])

            # Filter down to the last 30 days
            recent_cutoff = datetime.now().timestamp() - (30 * 86400)
            filtered = [
                b for b in settled_data
                if b.get("resultAwardedDate", 0) >= recent_cutoff
            ]

            for bet in filtered:
                all_results.append(process_mobile_bet(bet, "Settled"))
        else:
            st.warning(f"Settled request failed: HTTP {r.status_code}")
    except Exception as e:
        st.warning(f"Error fetching Settled bets: {e}")

    return all_results


def process_mobile_bet(bet, bet_label):
    """
    Transform FanDuel mobile API bet structure into our table row.
    """

    desc = bet.get("description", "Unknown Bet")
    stake = float(bet.get("stake", 0))
    odds = int(bet.get("oddsAmerican", 0))

    result_raw = bet.get("result", "").upper()
    if result_raw == "WON":
        result = "Win"
    elif result_raw == "LOST":
        result = "Loss"
    elif result_raw == "PUSH":
        result = "Push"
    else:
        result = "Pending"

    # Profit calculation
    if result == "Win":
        profit = stake * (odds / 100) if odds > 0 else stake / (abs(odds) / 100)
    elif result == "Loss":
        profit = -stake
    else:
        profit = 0

    return {
        "Date": datetime.now().strftime("%Y-%m-%d"),
        "Sport": "Auto",
        "Bet Type": bet_label,
        "Player/Team": desc,
        "Odds": odds,
        "Stake": stake,
        "Result": result,
        "Profit": profit,
        "Imported": True
    }


# ======================
# TRIGGER IMPORT
# ======================
if uploaded_cookies:
    cookies = load_cookies(uploaded_cookies)

    if cookies:
        st.info("Authenticating with FanDuel Mobile API…")

        session = create_mobile_session(cookies)

        st.info("Fetching active + recent settled bets...")
        bets = fetch_mobile_bets(session)

        if len(bets) > 0:
            imported_df = pd.DataFrame(bets)
            df = pd.concat([df, imported_df], ignore_index=True)

            df.drop_duplicates(
                subset=["Player/Team", "Stake", "Odds"],
                keep="first",
                inplace=True
            )

            df.to_csv(DATA_FILE, index=False)

            st.success(f"Imported {len(imported_df)} bets from FanDuel!")
        else:
            st.warning("No bets found. Cookies may be expired or no recent bets.")


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
