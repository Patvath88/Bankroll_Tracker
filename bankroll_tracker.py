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
