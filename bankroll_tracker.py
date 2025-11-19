import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

DATA_FILE = "bets.csv"

# ------------------------------------
# Load or initialize data
# ------------------------------------
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=[
        "Date", "Sport", "Bet Type", "Player/Team", "Odds", 
        "Stake", "Result", "Profit", "Imported"
    ])
    df.to_csv(DATA_FILE, index=False)


st.set_page_config(page_title="Bankroll Tracker", layout="wide")
st.title("🔥 Enhanced Sports Betting Bankroll Tracker")


# ------------------------------------
# Sidebar – Bankroll Summary
# ------------------------------------
st.sidebar.header("📊 Bankroll Summary")

total_profit = df["Profit"].sum()
starting_bankroll = st.sidebar.number_input("Starting Bankroll", value=1000)

bankroll = starting_bankroll + total_profit
wins = df[df["Profit"] > 0].shape[0]
losses = df[df["Profit"] < 0].shape[0]
win_rate = (wins / max(1, wins + losses)) * 100

st.sidebar.metric("Current Bankroll", f"${bankroll:.2f}")
st.sidebar.metric("Total Profit", f"${total_profit:.2f}")
st.sidebar.metric("Win Rate", f"{win_rate:.1f}%")


# ------------------------------------
# Unit Sizing Tools
# ------------------------------------
st.subheader("📐 Unit Sizing Tools")

colU1, colU2, colU3 = st.columns(3)

with colU1:
    kelly_edge = st.number_input("Estimated Edge (%)", value=5.0)
with colU2:
    kelly_win_prob = st.number_input("Win Probability (%)", value=55.0)
with colU3:
    fixed_unit = st.number_input("Fixed Unit Size ($)", value=25.0)

def kelly_fraction(win_prob, odds):
    decimal_odds = (odds / 100) + 1 if odds > 0 else (100 / abs(odds)) + 1
    p = win_prob / 100
    b = decimal_odds - 1  
    return (b * p - (1 - p)) / b

def recommend_stake(odds):
    k_fraction = kelly_fraction(kelly_win_prob, odds)
    k_fraction = max(0, k_fraction)

    kelly_stake = bankroll * k_fraction
    risk_percent_stake = bankroll * (kelly_edge / 100)

    return kelly_stake, risk_percent_stake, fixed_unit


# ------------------------------------
# Manual Bet Entry
# ------------------------------------
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
    st.success("Bet Added!")


# ------------------------------------
# FanDuel Auto-Importer
# ------------------------------------
st.subheader("🔁 Import Bets from FanDuel (Manual Login via Chrome)")

if st.button("Start FanDuel Importer"):
    st.info("Launching Chrome... please log into FanDuel manually.")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get("https://sportsbook.fanduel.com/my-bets")
    driver.maximize_window()

    st.warning("⚠️ Please log in to FanDuel.\nOnce logged in, stay on the 'My Bets' page.")
    time.sleep(15)

    # Scrape both Settled and Active
    bet_entries = []

    try:
        time.sleep(3)
        bets = driver.find_elements(By.CLASS_NAME, "bet-item")

        for b in bets:
            try:
                text = b.text.split("\n")
                date = datetime.today().strftime("%Y-%m-%d")
                desc = text[0]
                stake_line = [x for x in text if "Stake" in x][0]
                odds_line = [x for x in text if "@" in x][0]

                stake = float(stake_line.replace("Stake: $", ""))
                odds = int(odds_line.split("@")[1])

                # Determine result
                if "Won" in text:
                    result = "Win"
                elif "Lost" in text:
                    result = "Loss"
                else:
                    result = "Pending"

                if result == "Win":
                    profit = stake * (odds / 100) if odds > 0 else stake / (abs(odds) / 100)
                elif result == "Loss":
                    profit = -stake
                else:
                    profit = 0

                bet_entries.append({
                    "Date": date,
                    "Sport": "Auto",
                    "Bet Type": "Imported",
                    "Player/Team": desc,
                    "Odds": odds,
                    "Stake": stake,
                    "Result": result,
                    "Profit": profit,
                    "Imported": True
                })

            except:
                pass

        driver.quit()

        if bet_entries:
            imported_df = pd.DataFrame(bet_entries)
            df = pd.concat([df, imported_df], ignore_index=True)
            df.drop_duplicates(subset=["Player/Team", "Stake", "Odds"], keep="first", inplace=True)
            df.to_csv(DATA_FILE, index=False)

            st.success(f"Imported {len(imported_df)} FanDuel bets!")

        else:
            st.warning("No bets found or scraper could not read the layout.")

    except Exception as e:
        st.error(f"Scraper error: {e}")
        driver.quit()


# ------------------------------------
# Bet History
# ------------------------------------
st.subheader("📜 Bet History")
st.dataframe(df)


# ------------------------------------
# Profit Trend Chart
# ------------------------------------
if not df.empty:
    df_graph = df.copy()
    df_graph["Date"] = pd.to_datetime(df_graph["Date"])
    df_graph["Cumulative Profit"] = df_graph["Profit"].cumsum()

    st.subheader("📈 Profit Over Time")
    st.line_chart(df_graph[["Date", "Cumulative Profit"]].set_index("Date"))
