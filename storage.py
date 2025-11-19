import json
import os

DATA_FILE = "bets.json"

# ------------------------------------------------------------
# LOAD BETS
# ------------------------------------------------------------
def load_bets():
    if not os.path.exists(DATA_FILE):
        save_bets([])  # create empty file
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# ------------------------------------------------------------
# SAVE BETS
# ------------------------------------------------------------
def save_bets(bets):
    with open(DATA_FILE, "w") as f:
        json.dump(bets, f, indent=4)

# ------------------------------------------------------------
# ADD BET
# ------------------------------------------------------------
def add_bet(bet):
    bets = load_bets()
    bets.append(bet)
    save_bets(bets)

# ------------------------------------------------------------
# DELETE BET
# ------------------------------------------------------------
def delete_bet(index):
    bets = load_bets()
    if 0 <= index < len(bets):
        bets.pop(index)
    save_bets(bets)
