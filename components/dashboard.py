import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime
from utils import units_won
from fanduel_theme import FD_BLUE, FD_GREEN, FD_RED


# -------------------------------------------------------------
# Convert storage list → DataFrame
# -------------------------------------------------------------
def bets_to_df(bets: list) -> pd.DataFrame:
    if len(bets) == 0:
        return pd.DataFrame()

    df = pd.DataFrame(bets)
    df["stake"] = df["stake"].astype(float)
    df["to_win"] = df["to_win"].astype(float)
    df["payout"] = df["payout"].astype(float)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["profit"] = df["to_win"]  # FanDuel Method: profit = to_win for wins (or 0 for losses)
    df["result"] = "Unknown"

    # Assign results based on profit (or future editing)
    df.loc[df["profit"] > 0, "result"] = "WIN"
    df.loc[df["profit"] == 0, "result"] = "LOSS"

    return df


# -------------------------------------------------------------
# DASHBOARD PAGE
# -------------------------------------------------------------
def dashboard_page(bets: list, unit_size: float):
    st.header("📊 Performance Dashboard")

    if len(bets) == 0:
        st.info("No bets added yet.")
        return

    df = bets_to_df(bets)

    # -------------------------------
    # SUMMARY METRICS
    # -------------------------------
    total_profit = df["profit"].sum()
    win_rate = (df["result"] == "WIN").mean() * 100
    total_units = units_won(total_profit, unit_size)
    avg_odds = df["odds"].astype(float).mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Profit", f"${round(total_profit, 2)}")
    with col2:
        st.metric("Win Rate", f"{round(win_rate, 2)}%")
    with col3:
        st.metric("Units Won", f"{round(total_units, 2)}u")
    with col4:
        st.metric("Average Odds", f"{round(avg_odds, 2)}")

    st.markdown("---")

    # -------------------------------
    # PROFIT OVER TIME CHART
    # -------------------------------
    df_sorted = df.sort_values("timestamp")
    df_sorted["cumulative_profit"] = df_sorted["profit"].cumsum()

    st.subheader("📈 Profit Over Time")
    line_chart = alt.Chart(df_sorted).mark_line(color=FD_BLUE, strokeWidth=3).encode(
        x="timestamp:T",
        y="cumulative_profit:Q",
        tooltip=["timestamp:T", "cumulative_profit:Q"]
    )
    st.altair_chart(line_chart, use_container_width=True)

    st.markdown("---")

    # -------------------------------
    # PROFIT BY SPORT
    # -------------------------------
    st.subheader("🏆 Profit by Sport")
    sport_profit = df.groupby("sport")["profit"].sum().reset_index()

    bar_chart = alt.Chart(sport_profit).mark_bar(color=FD_GREEN).encode(
        x=alt.X("profit:Q", title="Profit ($)"),
        y=alt.Y("sport:N", sort="-x", title="Sport"),
        tooltip=["sport", "profit"]
    )
    st.altair_chart(bar_chart, use_container_width=True)

    st.markdown("---")

    # -------------------------------
    # PROFIT BY SPORTSBOOK
    # -------------------------------
    st.subheader("🏦 Profit by Sportsbook")
    book_profit = df.groupby("sportsbook")["profit"].sum().reset_index()

    bar_chart2 = alt.Chart(book_profit).mark_bar(color=FD_BLUE).encode(
        x=alt.X("profit:Q", title="Profit ($)"),
        y=alt.Y("sportsbook:N", sort="-x", title="Sportsbook"),
        tooltip=["sportsbook", "profit"]
    )
    st.altair_chart(bar_chart2, use_container_width=True)

    st.markdown("---")

    # -------------------------------
    # ODDS DISTRIBUTION
    # -------------------------------
    st.subheader("📉 Odds Distribution")
    df["odds"] = df["odds"].astype(int)
    hist = alt.Chart(df).mark_bar(color=FD_BLUE).encode(
        x=alt.X("odds:Q", bin=alt.Bin(maxbins=20), title="American Odds"),
        y=alt.Y("count()", title="Count"),
        tooltip=["count()"]
    )
    st.altair_chart(hist, use_container_width=True)

    st.markdown("---")

    # -------------------------------
    # DAILY PROFIT HEATMAP (optional)
    # -------------------------------
    st.subheader("📆 Daily Profit Heatmap")

    df["date"] = df["timestamp"].dt.date
    daily_profit = df.groupby("date")["profit"].sum().reset_index()

    heatmap = alt.Chart(daily_profit).mark_rect().encode(
        x=alt.X("date:T", title="Date"),
        y=alt.value(20),
        color=alt.Color("profit:Q", scale=alt.Scale(scheme="greenblue")),
        tooltip=["date:T", "profit:Q"]
    ).properties(height=100)

    st.altair_chart(heatmap, use_container_width=True)
