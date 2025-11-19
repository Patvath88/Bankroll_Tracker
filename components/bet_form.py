import streamlit as st
from datetime import datetime
from utils import (
    implied_probability,
    expected_value,
    calculate_to_win,
    calculate_payout,
    kelly_stake,
    kelly_half,
    kelly_quarter,
)
from fanduel_theme import FD_BLUE, FD_GREEN, FD_RED, FD_GRAY


# -------------------------------------------------------------
# UNIVERSAL PROP LIST (covers NBA, MLB, NFL & more)
# -------------------------------------------------------------
UNIVERSAL_STATS = [
    "Points", "Rebounds", "Assists", "3-Pointers", "Steals", "Blocks",
    "Hits", "Home Runs", "RBIs", "Total Bases", "Stolen Bases",
    "Passing Yards", "Rushing Yards", "Receiving Yards",
    "Receptions", "Touchdowns", "Completions", "Field Goals",
    "Shots", "Goals", "Saves",
    "Custom"
]


# -------------------------------------------------------------
# PARLAY LEG INPUT BLOCK
# -------------------------------------------------------------
def render_leg(index: int):
    """Render one parlay leg input row."""
    st.markdown(f"### Leg {index + 1}")

    col1, col2 = st.columns([1.5, 1.5])
    with col1:
        player = st.text_input(f"Player/Team (Leg {index+1})", key=f"player_{index}")
    with col2:
        stat = st.selectbox(
            f"Stat Type (Leg {index+1})",
            UNIVERSAL_STATS,
            key=f"stat_{index}"
        )

    col3, col4, col5 = st.columns([1, 1, 1])
    with col3:
        line = st.text_input(f"Line (Leg {index+1})", key=f"line_{index}")
    with col4:
        ou = st.selectbox(
            f"O/U (Leg {index+1})",
            ["Over", "Under"],
            key=f"ou_{index}"
        )
    with col5:
        leg_odds = st.text_input(
            f"Leg Odds (Optional, Leg {index+1})",
            key=f"legodds_{index}"
        )

    return {
        "player": player,
        "stat": stat,
        "line": line,
        "ou": ou,
        "leg_odds": leg_odds,
    }


# -------------------------------------------------------------
# MAIN FORM
# -------------------------------------------------------------
def bet_form(add_bet_callback):
    """Renders the bet entry UI (straights + parlays)."""

    st.header("📥 Add a New Bet")

    # ----------------------------------------------------------
    # General bet info
    # ----------------------------------------------------------
    sport = st.selectbox("Sport", ["NBA", "MLB", "NFL", "NHL", "NCAAB", "NCAAF", "Tennis", "Soccer", "UFC", "Golf", "Other"])
    sportsbook = st.selectbox("Sportsbook", ["FanDuel"])
    bet_type = st.selectbox("Bet Type", ["Straight", "Parlay"])

    # ----------------------------------------------------------
    # Straight Bet Form
    # ----------------------------------------------------------
    if bet_type == "Straight":
        odds = st.number_input("Odds (American)", step=1)
        stake = st.number_input("Stake ($)", min_value=0.0, step=1.0)

        ip = implied_probability(odds)
        to_win = calculate_to_win(stake, odds)
        payout = calculate_payout(stake, odds)

        st.markdown(f"**Implied Probability:** `{round(ip*100, 2)}%`")
        st.markdown(f"**To Win:** `${to_win}`")
        st.markdown(f"**Total Payout:** `${payout}`")

        # EV + Kelly
        st.subheader("📊 EV + Kelly Analysis")
        user_win_prob = ip  # FD Method — IP becomes actual probability

        ev = expected_value(stake, odds, user_win_prob)
        k_full = kelly_stake(1000, user_win_prob, odds)
        k_half_val = kelly_half(1000, user_win_prob, odds)
        k_quarter_val = kelly_quarter(1000, user_win_prob, odds)

        st.markdown(f"**EV:** `${round(ev, 2)}`")
        st.markdown(f"**Full Kelly:** `${round(k_full, 2)}`")
        st.markdown(f"**Half Kelly:** `${round(k_half_val, 2)}`")
        st.markdown(f"**Quarter Kelly:** `${round(k_quarter_val, 2)}`")

        notes = st.text_area("Notes (Optional)")

        if st.button("➕ Add Bet", use_container_width=True):
            bet = {
                "type": "Straight",
                "sport": sport,
                "sportsbook": sportsbook,
                "odds": odds,
                "stake": stake,
                "to_win": to_win,
                "payout": payout,
                "legs": [],
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            }
            add_bet_callback(bet)
            st.success("Straight bet added!")

    # ----------------------------------------------------------
    # PARLAY Bet Form
    # ----------------------------------------------------------
    else:
        num_legs = st.number_input("Number of Parlay Legs", min_value=2, max_value=25, step=1)

        legs = []
        for i in range(num_legs):
            with st.container():
                leg = render_leg(i)
                legs.append(leg)
                st.markdown("---")

        odds = st.number_input("Overall Parlay Odds (American)", step=1)
        stake = st.number_input("Stake ($)", min_value=0.0, step=1.0)

        ip = implied_probability(odds)
        to_win = calculate_to_win(stake, odds)
        payout = calculate_payout(stake, odds)

        st.markdown(f"**Implied Probability:** `{round(ip*100, 2)}%`")
        st.markdown(f"**To Win:** `${to_win}`")
        st.markdown(f"**Total Payout:** `${payout}`")

        # EV + Kelly
        st.subheader("📊 EV + Kelly Analysis")
        user_win_prob = ip  # FD method

        ev = expected_value(stake, odds, user_win_prob)
        k_full = kelly_stake(1000, user_win_prob, odds)
        k_half_val = kelly_half(1000, user_win_prob, odds)
        k_quarter_val = kelly_quarter(1000, user_win_prob, odds)

        st.markdown(f"**EV:** `${round(ev, 2)}`")
        st.markdown(f"**Full Kelly:** `${round(k_full, 2)}`")
        st.markdown(f"**Half Kelly:** `${round(k_half_val, 2)}`")
        st.markdown(f"**Quarter Kelly:** `${round(k_quarter_val, 2)}`")

        notes = st.text_area("Notes (Optional)")

        if st.button("➕ Add Parlay", use_container_width=True):
            bet = {
                "type": "Parlay",
                "sport": sport,
                "sportsbook": sportsbook,
                "odds": odds,
                "stake": stake,
                "to_win": to_win,
                "payout": payout,
                "legs": legs,
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            }
            add_bet_callback(bet)
            st.success("Parlay added!")

