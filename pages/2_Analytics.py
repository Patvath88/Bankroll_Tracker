import streamlit as st
import pandas as pd
import plotly.express as px
from storage import get_all_bets

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("📈 Analytics Dashboard")

bets = get_all_bets()

if not bets:
    st.info("Add bets to view analytics.")
    st.stop()

df = pd.DataFrame(bets)
df["date"] = pd.to_datetime(df["timestamp"]).dt.date

def profit(row):
    if row["result"] == "Pending":
        return 0
    if row["result"] == "Won":
        return row["payout"] - row["stake"]
    if row["result"] == "Lost":
        return -row["stake"]
    return 0

df["profit"] = df.apply(profit, axis=1)

total_profit = df["profit"].sum()
total_staked = df["stake"].sum()
roi = (total_profit / total_staked * 100) if total_staked > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("Profit", f"${round(total_profit,2)}")
col2.metric("Total Staked", f"${round(total_staked,2)}")
col3.metric("ROI", f"{round(roi,2)}%")

st.subheader("Profit by Sport")
fig = px.bar(df.groupby("sport")["profit"].sum().reset_index(), x="sport", y="profit")
st.plotly_chart(fig)

st.subheader("Daily Profit")
fig2 = px.line(df.groupby("date")["profit"].sum().reset_index(), x="date", y="profit")
st.plotly_chart(fig2)
