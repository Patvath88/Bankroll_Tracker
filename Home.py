import streamlit as st
from storage import get_bankroll, set_bankroll, add_bet
from odds_engine import (
    calculate_to_win_and_payout,
    calculate_parlay_odds,
    american_to_implied_prob,
    calculate_kelly,
)

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🏠 Add Bets")

# ---------------------------------------------------------
# BANKROLL CHECK
# ---------------------------------------------------------
bankroll = get_bankroll()
if bankroll is None:
    st.warning("Please enter your starting bankroll (saved permanently).")
    new_br = st.number_input("Enter bankroll ($):", value=1000)
    if st.button("Save Bankroll"):
        set_bankroll(new_br)
        st.success("Bankroll saved!")
        st.rerun()
else:
    st.success(f"Current Bankroll: ${bankroll}")

# ---------------------------------------------------------
# SELECT BET TYPE
# ---------------------------------------------------------
bet_type = st.selectbox("Bet Type", ["Straight", "Parlay"])

# ---------------------------------------------------------
# STRAIGHT BET
# ---------------------------------------------------------
if bet_type == "Straight":
    sport = st.selectbox("Sport", ["NBA", "NFL", "MLB", "NHL", "Soccer", "NCAAB", "NCAAF"])

    odds = st.number_input("Odds (American)", value=-110)
    stake = st.number_input("Stake ($)", value=10.0)

    to_win, payout = calculate_to_win_and_payout(odds, stake)
    imp = american_to_implied_prob(odds)
    kf, kelly_stake = calculate_kelly(bankroll, odds)

    st.metric("To Win", f"${to_win}")
    st.metric("Payout", f"${payout}")
    st.metric("Implied Prob", f"{round(imp*100,2)}%")
    st.metric("Kelly Stake", f"${kelly_stake}")

    if st.button("Add Straight Bet"):
        add_bet({
            "sport": sport,
            "type": "Straight",
            "stake": stake,
            "odds": odds,
            "to_win": to_win,
            "payout": payout,
            "legs": [],
            "result": "Pending"
        })
        st.success("Straight bet added!")

# ---------------------------------------------------------
# PARLAY BET
# ---------------------------------------------------------
else:
    num_legs = st.slider("Number of Legs", 1, 25, 2)

    legs = []
    leg_odds = []

    for i in range(num_legs):
        st.subheader(f"Leg {i+1}")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            player = st.text_input(f"Player/Team {i+1}", key=f"p{i}")
        with col2:
            prop = st.text_input(f"Prop {i+1}", key=f"pr{i}")
        with col3:
            prop_type = st.text_input(f"Type {i+1}", key=f"t{i}")
        with col4:
            line = st.text_input(f"Line {i+1}", key=f"l{i}")
        with col5:
            ou = st.selectbox(f"O/U {i+1}", ["Over", "Under"], key=f"ou{i}")

        odds_leg = st.text_input(f"Leg Odds {i+1}", key=f"od{i}")
        leg_odds.append(float(odds_leg) if odds_leg else -110)

        legs.append({
            "player": player,
            "prop": prop,
            "type": prop_type,
            "line": line,
            "ou": ou,
            "odds": odds_leg if odds_leg else None
        })

    overall_odds = calculate_parlay_odds(leg_odds)

    st.metric("Parlay Odds", overall_odds)

    stake = st.number_input("Stake ($)", value=10.0)
    to_win, payout = calculate_to_win_and_payout(overall_odds, stake)
    kf, kelly_stake = calculate_kelly(bankroll, overall_odds)

    st.metric("To Win", f"${to_win}")
    st.metric("Payout", f"${payout}")
    st.metric("Kelly Stake", f"${kelly_stake}")

    if st.button("Add Parlay Bet"):
        add_bet({
            "sport": "Multiple",
            "type": "Parlay",
            "stake": stake,
            "odds": overall_odds,
            "to_win": to_win,
            "payout": payout,
            "legs": legs,
            "result": "Pending"
        })
        st.success("Parlay added!")
