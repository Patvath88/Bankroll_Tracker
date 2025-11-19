import streamlit as st
from odds_engine import (
    calculate_to_win_and_payout,
    calculate_parlay_odds,
    american_to_implied_prob,
    calculate_kelly,
)
from storage import add_bet


# -------------------------------------------------------------------
# BET INPUT SECTION
# -------------------------------------------------------------------

st.header("➕ Add a Bet (Straight or Parlay)")

bet_type = st.selectbox("Bet Type", ["Straight", "Parlay"])


# -------------------------------------------------------------------
# STRAIGHT BET
# -------------------------------------------------------------------
if bet_type == "Straight":
    col1, col2, col3 = st.columns(3)

    with col1:
        sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "NHL", "NCAAB", "NCAAF", "Soccer"])
    with col2:
        odds = st.number_input("Odds (American)", value=-110, step=1)
    with col3:
        stake = st.number_input("Stake ($)", value=10.0, step=1.0)

    # Auto math
    to_win, payout = calculate_to_win_and_payout(odds, stake)
    imp_prob = american_to_implied_prob(odds)
    kf, kelly_stake = calculate_kelly(bankroll=1000, odds=odds)

    st.markdown(f"**To Win:** ${to_win}")
    st.markdown(f"**Payout:** ${payout}")
    st.markdown(f"**Implied Probability:** {round(imp_prob*100,2)}%")
    st.markdown(f"**Kelly Stake Suggestion (example bankroll=1000):** ${kelly_stake}")

    # Submit button
    if st.button("Add Straight Bet"):
        bet_data = {
            "sport": sport,
            "type": "Straight",
            "odds": odds,
            "stake": stake,
            "to_win": to_win,
            "payout": payout,
            "legs": [],
            "result": "Pending",
        }
        bet_id = add_bet(bet_data)
        st.success(f"Straight bet added! ID #{bet_id}")


# -------------------------------------------------------------------
# PARLAY BET
# -------------------------------------------------------------------
else:
    st.subheader("🧩 Parlay Builder")

    num_legs = st.slider("Number of Legs", 1, 25, 2)

    legs = []

    for i in range(num_legs):
        st.markdown(f"### Leg {i+1}")

        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            player = st.text_input(f"Player/Team {i+1}", key=f"player_{i}")
        with c2:
            prop = st.text_input(f"Prop {i+1}", key=f"prop_{i}")
        with c3:
            prop_type = st.text_input(f"Type {i+1}", key=f"type_{i}")
        with c4:
            line = st.text_input(f"Line {i+1}", key=f"line_{i}")
        with c5:
            ou = st.selectbox(f"O/U {i+1}", ["Over", "Under"], key=f"ou_{i}")

        odds_for_leg = st.text_input(f"Leg Odds (optional) {i+1}", key=f"leg_odds_{i}")

        legs.append({
            "player": player,
            "prop": prop,
            "type": prop_type,
            "line": line,
            "ou": ou,
            "odds": float(odds_for_leg) if odds_for_leg else None
        })

        st.divider()


    # PARLAY ODDS CALCULATION
    st.subheader("📊 Parlay Odds & Payout")
    overall_odds = st.number_input("Parlay Odds (American)", value=-110, step=1)

    stake = st.number_input("Stake ($)", value=10.0, step=1.0)

    to_win, payout = calculate_to_win_and_payout(overall_odds, stake)
    imp_prob = american_to_implied_prob(overall_odds)
    kf, kelly_stake = calculate_kelly(1000, overall_odds)

    st.markdown(f"**To Win:** ${to_win}")
    st.markdown(f"**Payout:** ${payout}")
    st.markdown(f"**Implied Probability:** {round(imp_prob*100,2)}%")
    st.markdown(f"**Kelly Stake Suggestion (example bankroll=1000):** ${kelly_stake}")


    # SUBMIT PARLAY
    if st.button("Add Parlay Bet"):
        bet_data = {
            "sport": "Multiple",
            "type": "Parlay",
            "odds": overall_odds,
            "stake": stake,
            "to_win": to_win,
            "payout": payout,
            "legs": legs,
            "result": "Pending",
        }
        bet_id = add_bet(bet_data)
        st.success(f"Parlay added! ID #{bet_id}")
import streamlit as st
from storage import get_all_bets, delete_bet
from datetime import datetime


# -------------------------------------------------------------------
# BET HISTORY SECTION
# -------------------------------------------------------------------

st.header("📜 Bet History")

bets = get_all_bets()

if not bets:
    st.info("No bets added yet.")
else:
    for bet in sorted(bets, key=lambda x: x["timestamp"], reverse=True):

        # ----------------------------
        # HEADER ROW
        # ----------------------------
        with st.container():
            st.markdown(
                """
                <style>
                .bet-card {
                    background-color: #0a0f24;
                    padding: 18px;
                    border-radius: 14px;
                    margin-bottom: 18px;
                    border: 1px solid #1e2a48;
                }
                .bet-header {
                    font-size: 20px;
                    font-weight: 700;
                    color: white;
                }
                .bet-sub {
                    font-size: 14px;
                    color: #9bb0d4;
                }
                .bet-divider {
                    border-bottom: 1px solid #1e2a48;
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
                .leg-box {
                    background-color: #131a33;
                    padding: 10px;
                    border-radius: 10px;
                    margin-top: 8px;
                    border: 1px solid #1e2a48;
                }
                </style>
                """,
                unsafe_allow_html=True
            )

            st.markdown("<div class='bet-card'>", unsafe_allow_html=True)

            # ----------------------------
            # TOP LINE (Bet Type + Sport + Date)
            # ----------------------------
            date = datetime.fromisoformat(bet["timestamp"]).strftime("%b %d, %Y %I:%M %p")
            sport_display = bet["sport"] if bet["sport"] != "Multiple" else "Multi-Sport"

            st.markdown(
                f"""
                <div class='bet-header'>{bet['type']} Bet — {sport_display}</div>
                <div class='bet-sub'>{date}</div>
                <div class='bet-divider'></div>
                """,
                unsafe_allow_html=True
            )

            # ----------------------------
            # BET SUMMARY ROW
            # ----------------------------
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Odds", bet["odds"])
            with col2:
                st.metric("Stake", f"${bet['stake']}")
            with col3:
                st.metric("To Win", f"${bet['to_win']}")
            with col4:
                st.metric("Payout", f"${bet['payout']}")

            # ----------------------------
            # PARLAY LEGS (expansion)
            # ----------------------------
            if bet["legs"]:
                with st.expander("View Parlay Legs"):
                    for idx, leg in enumerate(bet["legs"], start=1):
                        st.markdown(
                            f"""
                            <div class='leg-box'>
                                <b>Leg {idx}</b><br>
                                {leg['player']} — {leg['prop']}<br>
                                <i>{leg['type']} | Line: {leg['line']} | {leg['ou']}</i><br>
                                {f"Odds: {leg['odds']}" if leg['odds'] else ""}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

            # ----------------------------
            # DELETE BUTTON
            # ----------------------------
            if st.button(f"Delete Bet #{bet['id']}", key=f"del_{bet['id']}"):
                delete_bet(bet["id"])
                st.warning(f"Bet #{bet['id']} deleted.")
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
import pandas as pd
import streamlit as st
from storage import get_all_bets
import plotly.express as px
from datetime import datetime


# -------------------------------------------------------------------
# ANALYTICS SECTION
# -------------------------------------------------------------------

st.header("📈 Analytics Dashboard")

bets = get_all_bets()

if not bets:
    st.info("Add some bets to see your analytics.")
else:
    # Convert JSON list → DataFrame
    df = pd.DataFrame(bets)

    # Fix numeric columns
    df["stake"] = df["stake"].astype(float)
    df["payout"] = df["payout"].astype(float)
    df["to_win"] = df["to_win"].astype(float)
    df["odds"] = df["odds"].astype(float)

    # Date parsing
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date

    # --------------------
    # CALCULATE PROFIT
    # --------------------
    def compute_profit(row):
        if row["result"] == "Pending":
            return 0
        if row["result"] == "Won":
            return row["payout"] - row["stake"]
        if row["result"] == "Lost":
            return -row["stake"]
        if row["result"] == "Push":
            return 0
        return 0

    df["profit"] = df.apply(compute_profit, axis=1)

    # --------------------
    # SUMMARY METRICS
    # --------------------
    total_profit = round(df["profit"].sum(), 2)
    total_staked = round(df["stake"].sum(), 2)
    roi = round((total_profit / total_staked * 100), 2) if total_staked > 0 else 0
    units = round(total_profit / 100, 2)
    win_rate = round((len(df[df["result"] == "Won"]) / len(df[df["result"] != "Pending"])) * 100, 2) \
        if len(df[df["result"] != "Pending"]) > 0 else 0

    # KPI DASHBOARD
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🔥 Total Profit", f"${total_profit}")
    m2.metric("📊 ROI", f"{roi}%")
    m3.metric("🏆 Units Won", f"{units}u")
    m4.metric("🎯 Hit Rate", f"{win_rate}%")

    st.divider()

    # --------------------
    # SPORT BREAKDOWN
    # --------------------
    st.subheader("🏅 Profit by Sport")

    by_sport = df.groupby("sport")["profit"].sum().reset_index()
    fig = px.bar(by_sport, x="sport", y="profit", color="sport",
                 color_discrete_sequence=px.colors.qualitative.Vivid)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --------------------
    # DAILY PROFIT TREND
    # --------------------
    st.subheader("📆 Daily Profit Over Time")

    daily = df.groupby("date")["profit"].sum().reset_index()
    fig2 = px.line(daily, x="date", y="profit", markers=True)
    st.plotly_chart(fig2, use_container_width=True)

    st.divider()

    # --------------------
    # ODDS DISTRIBUTION
    # --------------------
    st.subheader("🎲 Odds Distribution")

    fig3 = px.histogram(df, x="odds", nbins=40, title="American Odds Distribution")
    st.plotly_chart(fig3, use_container_width=True)

    st.divider()

    # --------------------
    # AVERAGES
    # --------------------
    st.subheader("📌 Averages")

    avg_stake = df["stake"].mean().round(2)
    avg_odds = df["odds"].mean().round(2)

    c1, c2 = st.columns(2)
    c1.metric("💵 Average Stake", f"${avg_stake}")
    c2.metric("📉 Average Odds", avg_odds)

    st.divider()

    # --------------------
    # BEST SPORT
    # --------------------
    best_sport = by_sport.loc[by_sport["profit"].idxmax()]["sport"]
    st.success(f"🏅 **Most Profitable Sport:** {best_sport}")

    # --------------------
    # FILTERS
    # --------------------
    st.subheader("🔍 Filter Bets")

    f1, f2 = st.columns(2)
    filter_type = f1.selectbox("Type Filter", ["All", "Straight", "Parlay"])
    filter_sport = f2.selectbox("Sport Filter", ["All"] + sorted(df["sport"].unique()))

    df_filtered = df.copy()

    if filter_type != "All":
        df_filtered = df_filtered[df_filtered["type"] == filter_type]

    if filter_sport != "All":
        df_filtered = df_filtered[df_filtered["sport"] == filter_sport]

    st.dataframe(df_filtered[["date", "sport", "type", "stake", "odds", "payout", "profit"]])
