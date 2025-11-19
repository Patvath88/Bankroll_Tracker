import streamlit as st
import pandas as pd
import os
from datetime import datetime

# -----------------------------
# Initialize storage
# -----------------------------
DATA_FILE = "bets.csv"

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Date", "Sport", "Bet Type", "Player/Team", "Odds", 
        "Stake", "Result", "Profit"
    ])
    df.to_csv(DATA_FILE, index=False)

st.set_page_config(page_title="Bankroll Tracker", layout="wide")

st.title("🔥 Sports Betting Bankroll Tracker")
st.write("Track your wagers, profit/loss, and long-term performance.")

# -----------------------------
# Sidebar: Bankroll Overview
# -----------------------------
st.sidebar.header("📊 Bankroll Summary")

total_staked = df["Stake"].sum()
total_profit = df["Profit"].sum()
bankroll = 1000 + total_profit  # starting bankroll = $1000 (editable)

wins = df[df["Profit"] > 0].shape[0]
losses = df[df["Profit"] < 0].shape[0]
win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0

st.sidebar.metric("Total Staked", f"${total_staked:.2f}")
st.sidebar.metric("Total Profit", f"${total_profit:.2f}")
st.sidebar.metric("Current Bankroll", f"${bankroll:.2f}")
st.sidebar.metric("Win Rate", f"{win_rate:.1f}%")

# -----------------------------
# Enter New Bet
# -----------------------------
st.subheader("➕ Add New Bet")

with st.form("bet_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        date = st.date_input("Date", datetime.today())
        sport = st.selectbox("Sport", ["MLB", "NBA", "NFL", "NHL", "NCAAF", "NCAAB", "Other"])
    
    with col2:
        bet_type = st.text_input("Bet Type (HR, K, Spread, etc.)")
        player_team = st.text_input("Player/Team")

    with col3:
        odds = st.number_input("Odds (American)", step=1)
        stake = st.number_input("Stake ($)", step=1.0)
        result = st.selectbox("Result", ["Pending", "Win", "Loss", "Push"])

    submitted = st.form_submit_button("Add Bet")

# -----------------------------
# Process Bet Submission
# -----------------------------
if submitted:
    # Calculate profit based on odds
    if result == "Pending":
        profit = 0
    else:
        if result == "Push":
            profit = 0
        elif odds > 0:
            profit = stake * (odds / 100) if result == "Win" else -stake
        else:
            profit = stake / (abs(odds) / 100) if result == "Win" else -stake

    new_row = {
        "Date": str(date),
        "Sport": sport,
        "Bet Type": bet_type,
        "Player/Team": player_team,
        "Odds": odds,
        "Stake": stake,
        "Result": result,
        "Profit": profit,
    }

    df = df.append(new_row, ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("Bet added successfully!")

# -----------------------------
# Display Bet History
# -----------------------------
st.subheader("📜 Bet History")
st.dataframe(df)

# -----------------------------
# Profit Graph
# -----------------------------
st.subheader("📈 Profit Over Time")

if not df.empty:
    df_graph = df.copy()
    df_graph["Date"] = pd.to_datetime(df_graph["Date"])
    df_graph["Cumulative Profit"] = df_graph["Profit"].cumsum()

    st.line_chart(df_graph[["Date", "Cumulative Profit"]].set_index("Date"))
else:
    st.info("No bets added yet.")
