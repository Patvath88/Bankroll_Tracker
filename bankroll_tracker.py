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
