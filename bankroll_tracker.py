import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import easyocr
from PIL import Image
import re
import os

# =============================
# CONFIG
# =============================
st.set_page_config(page_title="Bankroll Tracker", layout="wide")

DATA_FILE = "bets.csv"

# =============================
# COLUMN SCHEMA (PERMANENT FIX)
# =============================
REQUIRED_COLUMNS = [
    "Date",
    "Sport",
    "Bet Type",
    "Player/Team",
    "Odds",
    "Stake",
    "Result",
    "Profit",
    "LegsJSON",
    "Imported"
]

if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)

    # Add missing columns
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # Remove extra columns
    df = df[REQUIRED_COLUMNS]

else:
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)

df.to_csv(DATA_FILE, index=False)


# =============================
# HELPER FUNCTIONS
# =============================

def calculate_odds(stake, odds):
    """Convert American odds → To Win + Payout (safe)."""
    if stake == 0 or odds == 0:
        return 0.0, stake

    if odds > 0:
        to_win = stake * (odds / 100)
    else:
        to_win = stake * (100 / abs(odds))

    payout = stake + to_win
    return round(to_win, 2), round(payout, 2)


def format_leg(line):
    """Smart leg formatter (Option 4)."""
    orig = line.strip()
    low = orig.lower()

    # Detect Over/Under
    ou_match = re.search(r'(over|under)\s*(\d+\.?\d*)', low)
    if ou_match:
        ou = ou_match.group(1).capitalize()
        num = ou_match.group(2)
        abbrev = f"{ou[0]}{num}"

        words = orig.split()
        player = " ".join(words[:2]) if len(words) >= 2 else orig

        metric = ""
        if "point" in low: metric = "Points"
        elif "rebound" in low: metric = "Rebounds"
        elif "assist" in low: metric = "Assists"

        if metric:
            return f"{player} — {ou} {num} {metric} ({abbrev})"

    # Moneyline
    if "ml" in low:
        return orig.replace("ML", "Moneyline")

    # TD, HR props
    for k in ["td", "touchdown", "hr", "homerun"]:
        if k in low:
            return orig

    return orig


# =============================
# OCR LOADING
# =============================
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)

reader = load_ocr()


def extract_ocr_text(image):
    arr = np.array(image)
    return "\n".join(reader.readtext(arr, detail=0))


# =============================
# PARLAY PARSER
# =============================
def parse_bet_slip(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    is_parlay = any("parlay" in l.lower() for l in lines)

    parsed = {
        "Bet Type": "Parlay" if is_parlay else "Straight",
        "Stake": 0,
        "Odds": 0,
        "Legs": [],
        "Player/Team": ""
    }

    # STAKE
    for line in lines:
        low = line.lower()
        if "stake" in low or "$" in low:
            nums = re.findall(r'\d+\.\d+|\d+', line.replace(",", ""))
            if nums:
                parsed["Stake"] = float(nums[-1])

    # ODDS
    for line in lines:
        match = re.search(r'(\+|\-)\d{3,4}', line)
        if match:
            parsed["Odds"] = int(match.group(0))
            break

    # LEGS
    leg_candidates = []
    for line in lines:
        low = line.lower()
        if any(x in low for x in ["stake", "payout", "win", "odds", "$"]):
            continue
        if len(line) > 3:
            leg_candidates.append(line)

    if is_parlay:
        parsed["Legs"] = [format_leg(l) for l in leg_candidates]
        parsed["Player/Team"] = "PARLAY"
    else:
        parsed["Player/Team"] = max(leg_candidates, key=len) if leg_candidates else ""

    return parsed


# =============================
# MANUAL ENTRY
# =============================
st.header("➕ Add Manual Bet")

with st.form("manual_bet"):
    col1, col2, col3 = st.columns(3)

    with col1:
        date = st.date_input("Date", datetime.today())
        sport = st.selectbox("Sport", ["NBA", "MLB", "NFL", "NHL", "Other"])
        bet_type = st.selectbox("Bet Type", ["Straight", "Parlay"])

    with col2:
        player_team = st.text_input("Player / Team / Description")
        odds = st.number_input("Odds (American)", step=1)
        stake = st.number_input("Stake ($)", min_value=0.0, step=1.0)

    with col3:
        to_win, payout = calculate_odds(stake, odds)
        st.write(f"**To Win:** ${to_win}")
        st.write(f"**Payout:** ${payout}")
        result = st.selectbox("Result", ["Pending", "Win", "Loss", "Push"])

    submitted = st.form_submit_button("Add Bet")

if submitted:
    if result == "Win":
        profit = to_win
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
        "LegsJSON": "",
        "Imported": False
    }

    df.loc[len(df)] = new_row
    df.to_csv(DATA_FILE, index=False)
    st.success("Manual bet added!")


# =============================
# OCR IMPORTER
# =============================
st.header("📸 Import Bet Slip")

uploaded_img = st.file_uploader("Upload bet slip image", type=["png", "jpg", "jpeg"])

if uploaded_img:
    image = Image.open(uploaded_img)
    text = extract_ocr_text(image)
    parsed = parse_bet_slip(text)

    st.subheader("Parsed Data")
    st.json(parsed)

    with st.form("import_form"):
        date = st.date_input("Date", datetime.today())
        sport = st.selectbox("Sport", ["NBA", "MLB", "NFL", "NHL", "Other"])
        odds = st.number_input("Odds", value=int(parsed["Odds"]))
        stake = st.number_input("Stake", value=float(parsed["Stake"]))

        to_win, payout = calculate_odds(stake, odds)
        st.write(f"**To Win:** ${to_win}")
        st.write(f"**Payout:** ${payout}")

        result = st.selectbox("Result", ["Pending", "Win", "Loss", "Push"])

        submitted_import = st.form_submit_button("Import Bet")

    if submitted_import:
        legs_json = ";".join(parsed["Legs"]) if parsed["Bet Type"] == "Parlay" else ""

        if result == "Win":
            profit = to_win
        elif result == "Loss":
            profit = -stake
        else:
            profit = 0

        new_row = {
            "Date": str(date),
            "Sport": sport,
            "Bet Type": parsed["Bet Type"],
            "Player/Team": parsed["Player/Team"],
            "Odds": odds,
            "Stake": stake,
            "Result": result,
            "Profit": profit,
            "LegsJSON": legs_json,
            "Imported": True
        }

        df.loc[len(df)] = new_row
        df.to_csv(DATA_FILE, index=False)
        st.success("Bet imported!")


# =============================
# BET HISTORY (CARD STYLE)
# =============================
st.header("📜 Bet History")

for idx, row in df.iterrows():

    to_win, payout = calculate_odds(row["Stake"], row["Odds"])

    st.markdown(f"""
    <div style="
        padding:18px;
        margin-bottom:12px;
        border-radius:12px;
        background-color:#202020;
        color:white;
    ">
      <h4>{row['Date']} — {row['Sport']} — {row['Bet Type']}</h4>

      <b>Bet:</b> {row['Player/Team']}<br>
      <b>Odds:</b> {row['Odds']}<br>
      <b>Stake:</b> ${row['Stake']}<br>
      <b>To Win:</b> ${to_win}<br>
      <b>Payout:</b> ${payout}<br>
      <b>Result:</b> {row['Result']}<br>
      <b>Profit:</b> ${row['Profit']}<br><br>
    """, unsafe_allow_html=True)

    # ----- PARLAY LEGS -----
    if isinstance(row["LegsJSON"], str) and row["LegsJSON"] != "":
        legs = row["LegsJSON"].split(";")
        st.markdown("**Legs:**")
        for i, leg in enumerate(legs, start=1):
            st.markdown(f"➡️ {i}) {leg}")

    # ----- DELETE BUTTON -----
    if st.button(f"Delete Bet #{idx}"):
        df.drop(idx, inplace=True)
        df.to_csv(DATA_FILE, index=False)
        st.experimental_rerun()
