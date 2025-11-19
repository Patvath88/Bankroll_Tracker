import streamlit as st
import easyocr
import numpy as np
from PIL import Image
import re

# -------------------------------------------------------------
# Initialize OCR Reader (only once)
# -------------------------------------------------------------
@st.cache_resource
def load_reader():
    return easyocr.Reader(["en"], gpu=False)


# -------------------------------------------------------------
# Extract odds (ex: +120, -150)
# -------------------------------------------------------------
def extract_odds(text):
    matches = re.findall(r"[\+\-]\d{3,4}", text)
    return matches[0] if matches else None


# -------------------------------------------------------------
# Extract stake (ex: $25.00)
# -------------------------------------------------------------
def extract_stake(text):
    match = re.search(r"\$\s?(\d+(\.\d{2})?)", text)
    if match:
        return float(match.group(1))
    return None


# -------------------------------------------------------------
# Identify bet type
# -------------------------------------------------------------
def extract_bet_type(text):
    if "parlay" in text.lower():
        return "Parlay"
    return "Straight"


# -------------------------------------------------------------
# Attempt to pull parlay legs (SUPER rough)
# -------------------------------------------------------------
def extract_parlay_legs(text):
    lines = text.split("\n")
    possible_legs = []

    for ln in lines:
        if any(keyword in ln.lower() for keyword in ["over", "under", "o/u", "points", "yards", "assists", "rebounds"]):
            possible_legs.append(ln.strip())

    return possible_legs[:25]


# -------------------------------------------------------------
# Main OCR importer function
# -------------------------------------------------------------
def ocr_importer():
    st.subheader("📸 OCR Bet Slip Importer (FanDuel)")

    uploaded = st.file_uploader("Upload FanDuel screenshot (PNG/JPG)", type=["png", "jpg", "jpeg"])

    if uploaded:
        image = Image.open(uploaded)
        st.image(image, caption="Uploaded Slip", use_container_width=True)

        # Load OCR model
        reader = load_reader()

        # Run OCR
        with st.spinner("Reading slip..."):
            result = reader.readtext(np.array(image), detail=0)
            extracted_text = "\n".join(result)

        st.markdown("### Extracted Text:")
        st.text(extracted_text)

        # Parse data
        odds = extract_odds(extracted_text)
        stake = extract_stake(extracted_text)
        bet_type = extract_bet_type(extracted_text)
        legs = extract_parlay_legs(extracted_text)

        st.markdown("---")
        st.subheader("📄 Auto-Detected Fields")

        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Bet Type:** `{bet_type}`")
            st.write(f"**Odds:** `{odds}`")
        with col2:
            st.write(f"**Stake:** `${stake}`")

        if bet_type == "Parlay" and legs:
            st.markdown("### 🧩 Detected Legs")
            for idx, lg in enumerate(legs):
                st.write(f"**Leg {idx+1}:** {lg}")

        # Return parsed values
        return {
            "raw_text": extracted_text,
            "bet_type": bet_type,
            "odds": odds,
            "stake": stake,
            "legs": legs
        }

    return None
