import streamlit as st
from fanduel_theme import FD_GREEN, FD_RED, FD_GRAY, FD_BLUE


# -----------------------------------------------------------
# Render a SINGLE FanDuel-style bet card
# -----------------------------------------------------------

def render_bet_card(bet: dict, index: int, delete_callback, edit_callback):
    """Render a single bet card (straight or parlay)."""

    # Profit logic
    profit = float(bet.get("to_win", 0)) if bet.get("grade", "") == "WIN" else 0
    if bet.get("grade", "") == "LOSS":
        profit = -float(bet.get("stake", 0))

    profit_color = FD_GREEN if profit > 0 else FD_RED

    with st.container():
        st.markdown('<div class="bet-card">', unsafe_allow_html=True)

        # --------------------------------------------
        # HEADER SECTION
        # --------------------------------------------
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(
                f"<div class='bet-header'>{bet.get('type', '').upper()}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div class='bet-subheader'>{bet.get('sport', '')} • {bet.get('sportsbook', '')}</div>",
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"<div class='bet-odds'>{bet.get('odds')}</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<hr>", unsafe_allow_html=True)

        # --------------------------------------------
        # STRAIGHT BET CONTENT
        # --------------------------------------------
        if bet["type"] == "Straight":
            st.markdown(f"**Stake:** ${bet['stake']}")
            st.markdown(f"**To Win:** ${bet['to_win']}")
            st.markdown(f"**Payout:** ${bet['payout']}")

            if "notes" in bet and bet["notes"].strip() != "":
                st.markdown(f"**Notes:** {bet['notes']}")

        # --------------------------------------------
        # PARLAY CONTENT
        # --------------------------------------------
        else:
            st.markdown(f"**Stake:** ${bet['stake']}")
            st.markdown(f"**To Win:** ${bet['to_win']}")
            st.markdown(f"**Payout:** ${bet['payout']}")

            st.markdown("### Parlay Legs")

            # Expandable section
            with st.expander("Show Parlay Legs"):
                st.markdown(
                    """
                    <table class="leg-table">
                        <tr>
                            <th>Player/Team</th>
                            <th>Stat</th>
                            <th>Line</th>
                            <th>O/U</th>
                            <th>Leg Odds</th>
                        </tr>
                    """,
                    unsafe_allow_html=True,
                )

                for leg in bet.get("legs", []):
                    st.markdown(
                        f"""
                        <tr>
                            <td>{leg.get('player', '')}</td>
                            <td>{leg.get('stat', '')}</td>
                            <td>{leg.get('line', '')}</td>
                            <td>{leg.get('ou', '')}</td>
                            <td>{leg.get('leg_odds', '')}</td>
                        </tr>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown("</table>", unsafe_allow_html=True)

            if "notes" in bet and bet["notes"].strip() != "":
                st.markdown(f"**Notes:** {bet['notes']}")

        # --------------------------------------------
        # FOOTER BUTTONS (EDIT + DELETE)
        # --------------------------------------------
        col1, col2 = st.columns([1, 1])

        with col1:
            edit_button = st.button("✏️ Edit", key=f"edit_{index}")
            if edit_button:
                edit_callback(index)

        with col2:
            delete_button = st.button("🗑 Delete", key=f"delete_{index}")
            if delete_button:
                delete_callback(index)

        st.markdown("</div>", unsafe_allow_html=True)
