import streamlit as st
from storage import get_all_bets, delete_bet
from datetime import datetime

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📜 Bet History")

bets = get_all_bets()

if not bets:
    st.info("No bets yet.")
else:
    for bet in sorted(bets, key=lambda x: x["timestamp"], reverse=True):
        st.markdown("<div class='bet-card'>", unsafe_allow_html=True)

        date = datetime.fromisoformat(bet["timestamp"]).strftime("%b %d, %Y %I:%M %p")
        st.markdown(f"### {bet['type']} — {bet['sport']}")
        st.caption(date)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Odds", bet["odds"])
        col2.metric("Stake", f"${bet['stake']}")
        col3.metric("To Win", f"${bet['to_win']}")
        col4.metric("Payout", f"${bet['payout']}")

        if bet["legs"]:
            with st.expander("View Parlay Legs"):
                for i, leg in enumerate(bet["legs"], 1):
                    st.write(
                        f"**Leg {i}** — {leg['player']} | {leg['prop']} | {leg['type']} | "
                        f"Line: {leg['line']} | {leg['ou']} {'' if leg['odds'] is None else f'| Odds: {leg['odds']}'}"
                    )

        if st.button(f"Delete Bet #{bet['id']}", key=f"del{bet['id']}"):
            delete_bet(bet["id"])
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
