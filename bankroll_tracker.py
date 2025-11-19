import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from PIL import Image
import easyocr
import os
import re

# =============================
# STREAMLIT CONFIG
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


def implied_probability_from_odds(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def kelly_stake(bankroll, odds, probability):
    if probability == 0:
        return 0

    b = american_to_decimal(odds) - 1
    p = probability
    q = 1 - p

    kelly_fraction = (p * b - q) / b

    if kelly_fraction < 0:
        return 0

    return bankroll * kelly_fraction


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
# LEG PARSING (TABLE FORMAT)
# =============================
def parse_leg_into_fields(leg):
    leg_low = leg.lower()

    # Extract odds
    odds_match = re.search(r'(\+|\-)\d{3,4}', leg)
    leg_odds = odds_match.group(0) if odds_match else "-"

    # Extract Over/Under
    ou = "-"
    if "over" in leg_low: ou = "O"
    elif "under" in leg_low: ou = "U"

    # Extract line value
    line_match = re.search(r'\d+\.?\d*', leg)
    line = line_match.group(0) if line_match else "-"

    # Identify stat based on keyword
    STAT_MAP = {
        "point": "Points",
        "pts": "Points",
        "rebound": "Rebounds",
        "reb": "Rebounds",
        "assist": "Assists",
        "ast": "Assists",
        "pra": "PRA",
        "pr ": "PR",
        " ra ": "RA",
        "3pt": "3PT Made",
        "hit": "Hits",
        "home run": "Home Runs",
        "hr": "Home Runs",
        "rbi": "RBIs",
        "tb": "Total Bases",
        "walk": "Walks",
        "strikeout": "Strikeouts",
        "passing": "Passing Yards",
        "rushing": "Rushing Yards",
        "receiving": "Receiving Yards",
        "completion": "Completions",
        "reception": "Receptions",
        "td": "TD Scored",
        "moneyline": "Moneyline",
        "ml": "Moneyline"
    }

    stat = "-"
    for key, val in STAT_MAP.items():
        if key in leg_low:
            stat = val
            break

    # Player/team extraction
    words = leg.split()
    player = " ".join(words[:2]) if len(words) >= 2 else leg

    # Build line display
    if stat == "Moneyline":
        line_display = "ML"
    else:
        line_display = f"{ou}{line}" if line != "-" else "-"

    return player, stat, line_display, leg_odds

# =============================
# UNIVERSAL STAT DROPDOWN (GROUPED)
# =============================
STAT_OPTIONS = {
    "--- NBA ---": [
        "Points", "Rebounds", "Assists", "PRA", "PR", "RA",
        "3PT Made", "Steals", "Blocks", "Turnovers"
    ],
    "--- MLB ---": [
        "Hits", "Home Runs", "RBIs", "Runs", "Total Bases",
        "Walks", "Strikeouts"
    ],
    "--- NFL ---": [
        "Passing Yards", "Receiving Yards", "Rushing Yards",
        "Completions", "Receptions", "TD Scored"
    ],
    "--- Universal ---": [
        "Moneyline", "Spread", "Alternate Spread", "Alternate Total"
    ]
}


# =============================
# MANUAL BET ENTRY
# =============================
st.header("➕ Add Manual Bet")

with st.form("manual_bet"):
    main_col1, main_col2, main_col3 = st.columns(3)

    # -----------------------------
    # MAIN BET INFO
    # -----------------------------
    with main_col1:
        date = st.date_input("Date", datetime.today())
        sport = st.selectbox("Sport", ["NBA", "MLB", "NFL", "NHL", "NCAAB", "NCAAF", "Other"])
        bet_type = st.selectbox("Bet Type", ["Straight", "Parlay"])

    with main_col2:
        player_team = st.text_input("Main Player / Team / Description")
        odds = st.number_input("Overall Odds (American)", step=1)

        # Auto implied probability
        auto_prob = implied_probability_from_odds(odds)
        probability = st.number_input(
            "Your Win Probability (0–1)",
            value=round(auto_prob, 3),
            min_value=0.0,
            max_value=1.0,
            step=0.01
        )

    with main_col3:
        # Kelly staking
        kelly = kelly_stake(bankroll, odds, probability)
        st.write(f"**Kelly Stake:** ${round(kelly,2)}")
        st.write(f"½ Kelly: ${round(kelly/2,2)}")
        st.write(f"¼ Kelly: ${round(kelly/4,2)}")

        stake = st.number_input(
            "Stake ($)",
            value=float(round(kelly/2,2)),
            min_value=0.0,
            step=1.0
        )

        result = st.selectbox("Result", ["Pending", "Win", "Loss", "Push"])

    # -----------------------------
    # PARLAY LEG BUILDER (UP TO 25 LEGS)
    # -----------------------------
    legs_data = []

    if bet_type == "Parlay":
        st.subheader("🧩 Parlay Legs")

        num_legs = st.number_input(
            "Number of Legs",
            min_value=1,
            max_value=25,
            value=1,
            step=1
        )

        for i in range(num_legs):
            st.markdown(f"### Leg {i+1}")

            leg_col1, leg_col2, leg_col3, leg_col4, leg_col5 = st.columns([2,2,1,1,1])

            with leg_col1:
                player_leg = st.text_input(f"Player/Team Name (Leg {i+1})")

            with leg_col2:
                # Build grouped selectbox
                options_list = []
                for category, vals in STAT_OPTIONS.items():
                    options_list.append(category)
                    options_list.extend(vals)

                stat_leg = st.selectbox(f"Stat Type (Leg {i+1})", options_list)

                # Prevent selecting category header
                if stat_leg in STAT_OPTIONS.keys():
                    st.warning("Please select a stat, not a header.")
                    stat_leg = "-"

            with leg_col3:
                line_leg = st.text_input(f"Line (Leg {i+1})")

            with leg_col4:
                ou_leg = st.selectbox(f"Over/Under (Leg {i+1})", ["Over", "Under", "-"])

            with leg_col5:
                odds_leg = st.text_input(f"Odds (Optional) (Leg {i+1})")

            leg_string = f"{player_leg} {stat_leg} {ou_leg} {line_leg} {odds_leg}"
            legs_data.append(leg_string)

    submitted = st.form_submit_button("Add Bet")

# =============================
# ADDING THE BET TO THE DATABASE
# =============================
if submitted:
    to_win, payout = calculate_odds(stake, odds)

    if result == "Win":
        profit = to_win
    elif result == "Loss":
        profit = -stake
    else:
        profit = 0

    legs_json = ";".join(legs_data) if bet_type == "Parlay" else ""

    new_row = {
        "Date": str(date),
        "Sport": sport,
        "Bet Type": bet_type,
        "Player/Team": player_team,
        "Odds": odds,
        "Stake": stake,
        "Result": result,
        "Profit": profit,
        "LegsJSON": legs_json,
        "Imported": False
    }

    df.loc[len(df)] = new_row
    df.to_csv(DATA_FILE, index=False)
    st.success("Bet added successfully!")
    st.experimental_rerun()
# =============================
# OCR IMPORTER
# =============================
st.header("📸 Import Bet Slip")

uploaded_img = st.file_uploader("Upload bet slip image", type=["png", "jpg", "jpeg"])

if uploaded_img:
    image = Image.open(uploaded_img)
    text = extract_ocr_text(image)

    st.subheader("Extracted Text")
    st.code(text)

    st.info("OCR Importer still works, but does not create parlay legs automatically. You may create legs manually.")

    st.warning("Review extracted text and manually create legs using the Manual Bet form above.")
# =============================
# BET HISTORY — FANDUEL-STYLE DISPLAY
# =============================
st.header("📜 Bet History")

for idx, row in df.iterrows():

    to_win, payout = calculate_odds(row["Stake"], row["Odds"])
    legs = row["LegsJSON"].split(";") if isinstance(row["LegsJSON"], str) and row["LegsJSON"] else []
    leg_count = len(legs)

    with st.expander(
        f"{row['Date']} • {row['Sport']} • {row['Bet Type']} "
        f"{f'({leg_count} legs)' if leg_count else ''}"
    ):

        # ----------------------------------------------------
        # MAIN BETSLIP CARD
        # ----------------------------------------------------
        st.markdown(f"""
        <div style="
            background-color:#0d1b2a;
            padding:20px;
            border-radius:12px;
            box-shadow: 0px 2px 10px rgba(0,0,0,0.35);
            color:white;
            font-size:16px;
            line-height:1.5;
            margin-bottom:20px;
        ">
            <div style="font-size:22px; font-weight:700; color:#1A73E8; margin-bottom:10px;">
                {row['Bet Type'].upper()} {f'— {leg_count} LEGS' if leg_count else ''}
            </div>

            <b>Player/Team:</b> {row['Player/Team']}<br>
            <b>Odds:</b> {row['Odds']}<br>
            <b>Stake:</b> ${row['Stake']}<br>
            <b>To Win:</b> ${to_win}<br>
            <b>Payout:</b> ${payout}<br>
            <b>Result:</b> {row['Result']}<br>
            <b>Profit:</b> ${row['Profit']}<br>
        </div>
        """, unsafe_allow_html=True)

        # ----------------------------------------------------
        # PARLAY LEGS TABLE (IF ANY)
        # ----------------------------------------------------
        if leg_count > 0:
            st.markdown("<h4 style='margin-top:0;'>Legs:</h4>", unsafe_allow_html=True)

            # Table header
            st.markdown("""
            <div style="
                display:flex;
                font-weight:700;
                padding:6px 0;
                border-bottom:1px solid #1A73E8;
                color:white;
            ">
                <div style="flex:2;">Player / Team</div>
                <div style="flex:2;">Stat</div>
                <div style="flex:1;">Line</div>
                <div style="flex:1;">Odds</div>
            </div>
            """, unsafe_allow_html=True)

            # Table rows
            for leg in legs:
                player, stat, line_ou, leg_odds = parse_leg_into_fields(leg)

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
                    <div style="flex:1;">{leg_odds}</div>
                </div>
                """, unsafe_allow_html=True)

        # ----------------------------------------------------
        # DELETE BUTTON
        # ----------------------------------------------------
        delete_col = st.columns([1,5])[0]
        with delete_col:
            if st.button(f"🗑 Delete Bet #{idx}", key=f"del_{idx}"):
                df.drop(idx, inplace=True)
                df.to_csv(DATA_FILE, index=False)
                st.experimental_rerun()

# END OF FILE
