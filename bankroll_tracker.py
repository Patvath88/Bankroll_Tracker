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
# COLUMN SCHEMA
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

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[REQUIRED_COLUMNS]

else:
    df = pd.DataFrame(columns=REQUIRED_COLUMNS)

df.to_csv(DATA_FILE, index=False)

# =============================
# SIDEBAR — BANKROLL
# =============================
st.sidebar.header("🏦 Bankroll Settings")
bankroll = st.sidebar.number_input("Current Bankroll ($)", value=1000.0, min_value=0.0, step=10.0)


# =============================
# HELPER FUNCTIONS
# =============================

def calculate_odds(stake, odds):
    if stake == 0 or odds == 0:
        return 0.0, stake

    if odds > 0:
        to_win = stake * (odds / 100)
    else:
        to_win = stake * (100 / abs(odds))

    payout = stake + to_win
    return round(to_win, 2), round(payout, 2)


def american_to_decimal(odds):
    if odds > 0:
        return 1 + (odds / 100)
    else:
        return 1 + (100 / abs(odds))


def kelly_stake(bankroll, odds, probability):
    if probability == 0:
        return 0

    b = american_to_decimal(odds) - 1
    p = probability
    q = 1 - p

    kelly_fraction = (p * b - q) / b

    if kelly_fraction < 0:
        return 0  # No bet recommended

    return bankroll * kelly_fraction


def format_leg(line):
    line = line.strip()
    return line


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

    # Stake
    for line in lines:
        low = line.lower()
        if "stake" in low or "$" in low:
            nums = re.findall(r'\d+\.\d+|\d+', line.replace(",", ""))
            if nums:
                parsed["Stake"] = float(nums[-1])

    # Odds
    for line in lines:
        match = re.search(r'(\+|\-)\d{3,4}', line)
        if match:
            parsed["Odds"] = int(match.group(0))
            break

    # Legs
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
# LEG PARSER FOR TABLE FORMAT
# =============================
def parse_leg_into_fields(leg):
    leg_low = leg.lower()

    # Odds
    odds_match = re.search(r'(\+|\-)\d{3,4}', leg)
    odds = odds_match.group(0) if odds_match else "-"

    # O/U
    ou = "-"
    if "over" in leg_low: ou = "O"
    elif "under" in leg_low: ou = "U"

    # Line
    line_match = re.search(r'\d+\.?\d*', leg)
    line = line_match.group(0) if line_match else "-"

    # Stat
    stat = "-"
    STAT_MAP = {
        "point": "Points",
        "pts": "Points",
        "rebound": "Rebounds",
        "reb": "Rebounds",
        "assist": "Assists",
        "ast": "Assists",
        "td": "Touchdown",
        "hr": "Home Run",
        "ml": "Moneyline",
        "moneyline": "Moneyline"
    }
    for k, v in STAT_MAP.items():
        if k in leg_low:
            stat = v
            break

    # Player/team
    words = leg.split()
    player = " ".join(words[:2]) if len(words) >= 2 else leg

    # Build line display
    if stat == "Moneyline":
        line_ou = "ML"
    else:
        line_ou = f"{ou}{line}" if line != "-" else "-"

    return player, stat, line_ou, odds


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
        probability = st.number_input("Your Win Probability (0-1)", min_value=0.0, max_value=1.0, step=0.01)

    with col2:
        player_team = st.text_input("Player / Team / Description")
        odds = st.number_input("Odds (American)", step=1)
        
        # Kelly stake
        kelly = kelly_stake(bankroll, odds, probability)
        st.write(f"**Kelly Stake:** ${round(kelly,2)}")
        st.write(f"½ Kelly: ${round(kelly/2,2)}")
        st.write(f"¼ Kelly: ${round(kelly/4,2)}")

        stake = st.number_input("Stake ($)", value=float(round(kelly/2,2)), min_value=0.0, step=1.0)

    with col3:
        to_win, payout = calculate_odds(stake, odds)
        st.write(f"**To Win:** ${to_win}")
        st.write(f"**Payout:** ${payout}")
        result = st.selectbox("Result", ["Pending", "Win", "Loss", "Push"])

    submitted = st.form_submit_button("Add Bet")

if submitted:
    if result == "Win": profit = to_win
    elif result == "Loss": profit = -stake
    else: profit = 0

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
    st.success("Bet added!")


# =============================
# OCR IMPORTER
# =============================
st.header("📸 Import Bet Slip")

uploaded_img = st.file_uploader("Upload bet slip image", type=["png", "jpg", "jpeg"])

if uploaded_img:
    image = Image.open(uploaded_img)
    text = extract_ocr_text(image)
    parsed = parse_bet_slip(text)

    st.json(parsed)

    with st.form("import_form"):
        date = st.date_input("Date", datetime.today())
        sport = st.selectbox("Sport", ["NBA", "MLB", "NFL", "NHL", "Other"])
        odds = st.number_input("Odds", value=int(parsed["Odds"]))
        stake = st.number_input("Stake", value=float(parsed["Stake"]))
        result = st.selectbox("Result", ["Pending", "Win", "Loss", "Push"])

        submitted_import = st.form_submit_button("Import Bet")

    if submitted_import:
        to_win, payout = calculate_odds(stake, odds)
        legs_json = ";".join(parsed["Legs"]) if parsed["Bet Type"] == "Parlay" else ""

        if result == "Win": profit = to_win
        elif result == "Loss": profit = -stake
        else: profit = 0

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
# BET HISTORY — FANDUEL STYLE
# =============================
st.header("📜 Bet History")

for idx, row in df.iterrows():

    to_win, payout = calculate_odds(row["Stake"], row["Odds"])

    legs = row["LegsJSON"].split(";") if isinstance(row["LegsJSON"], str) else []
    leg_count = len(legs)

    with st.expander(
        f"{row['Date']} • {row['Sport']} • {row['Bet Type']} "
        f"{f'({leg_count} legs)' if leg_count>0 else ''}"
    ):

        # Betslip card
        st.markdown(f"""
        <div style="
            background-color:#0d1b2a;
            padding:20px;
            border-radius:12px;
            box-shadow: 0px 2px 10px rgba(0,0,0,0.35);
            color:white;
            font-size:16px;
            line-height:1.5;
        ">
            <div style="font-size:22px; font-weight:700; color:#1A73E8; margin-bottom:10px;">
                {row['Bet Type'].upper()} {f'— {leg_count} LEGS' if leg_count else ''}
            </div>

            <b>Odds:</b> {row['Odds']}<br>
            <b>Stake:</b> ${row['Stake']}<br>
            <b>To Win:</b> ${to_win}<br>
            <b>Payout:</b> ${payout}<br>
            <b>Result:</b> {row['Result']}<br>
            <b>Profit:</b> ${row['Profit']}<br>
        </div>
        """, unsafe_allow_html=True)

        # LEG TABLE
        if leg_count > 0:
            st.markdown("<br><b style='font-size:18px;'>Legs:</b>", unsafe_allow_html=True)

            # Header
            st.markdown("""
            <div style="display:flex; font-weight:700; padding:6px 0; border-bottom:1px solid #1A73E8;">
                <div style="flex:2;">Player / Team</div>
                <div style="flex:2;">Stat</div>
                <div style="flex:1;">Line</div>
                <div style="flex:1;">Odds</div>
            </div>
            """, unsafe_allow_html=True)

            # Rows
            for leg in legs:
                player, stat, line_ou, odds_leg = parse_leg_into_fields(leg)

                st.markdown(f"""
                <div style="
                    display:flex;
                    padding:8px 0;
                    border-bottom:1px solid #333;
                    color:white;
                ">
                    <div style="flex:2;">{player}</div>
                    <div style="flex:2;">{stat}</div>
                    <div style="flex:1;">{line_ou}</div>
                    <div style="flex:1;">{odds_leg}</div>
                </div>
                """, unsafe_allow_html=True)

        # Delete button
        if st.button(f"🗑 Delete Bet #{idx}", key=f"del_{idx}"):
            df.drop(idx, inplace=True)
            df.to_csv(DATA_FILE, index=False)
            st.experimental_rerun()
