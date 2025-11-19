import json
import os
from datetime import datetime

# -----------------------------
# FILE PATHS
# -----------------------------
BET_DIR = "bets"
BET_FILE = os.path.join(BET_DIR, "bets.json")
BANKROLL_FILE = os.path.join(BET_DIR, "bankroll.json")

# -----------------------------
# ENSURE DIRECTORY EXISTS
# -----------------------------
if not os.path.exists(BET_DIR):
    os.makedirs(BET_DIR)

# -----------------------------
# CREATE EMPTY BETS FILE IF MISSING
# -----------------------------
if not os.path.exists(BET_FILE):
    with open(BET_FILE, "w") as f:
        json.dump([], f, indent=4)

# -----------------------------
# CREATE BANKROLL FILE IF MISSING
# -----------------------------
if not os.path.exists(BANKROLL_FILE):
    with open(BANKROLL_FILE, "w") as f:
        json.dump({"bankroll": None}, f, indent=4)


# =============================================================
# BANKROLL FUNCTIONS
# =============================================================

def get_bankroll():
    """Load bankroll from bankroll.json"""
    try:
        with open(BANKROLL_FILE, "r") as f:
            data = json.load(f)
        return data.get("bankroll")
    except:
        return None


def set_bankroll(amount):
    """Save bankroll permanently"""
    with open(BANKROLL_FILE, "w") as f:
        json.dump({"bankroll": amount}, f, indent=4)


# =============================================================
# BET STORAGE FUNCTIONS
# =============================================================

def load_bets():
    """Load all bets from bets.json"""
    try:
        with open(BET_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_bets(bets):
    """Save all bets back to bets.json"""
    with open(BET_FILE, "w") as f:
        json.dump(bets, f, indent=4)


def generate_bet_id(bets):
    """Create a unique bet ID"""
    if not bets:
        return 1
    return max(b["id"] for b in bets) + 1


def add_bet(bet_data):
    """Add a new bet and return its ID"""
    bets = load_bets()
    bet_id = generate_bet_id(bets)

    bet_data["id"] = bet_id
    bet_data["timestamp"] = datetime.now().isoformat()

    bets.append(bet_data)
    save_bets(bets)

    return bet_id


def delete_bet(bet_id):
    """Remove bet by ID"""
    bets = load_bets()
    updated = [b for b in bets if b["id"] != bet_id]
    save_bets(updated)


def get_all_bets():
    """Return all saved bets"""
    return load_bets()
