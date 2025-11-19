import json
import os
from datetime import datetime

DB_FILE = "bets_db.json"


# ----------------------------------------------------------------------------
# INTERNAL HELPERS
# ----------------------------------------------------------------------------

def _initialize_db():
    """Create the DB file if missing."""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({"bets": []}, f, indent=4)


def _load():
    """Load the DB JSON safely."""
    _initialize_db()
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Reset corrupted DB
        with open(DB_FILE, "w") as f:
            json.dump({"bets": []}, f, indent=4)
        return {"bets": []}


def _save(data):
    """Save JSON to disk."""
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ----------------------------------------------------------------------------
# PUBLIC API
# ----------------------------------------------------------------------------

def get_all_bets():
    """Return list of all bets."""
    db = _load()
    return db.get("bets", [])


def add_bet(bet_data):
    """
    Add a bet to the database.
    bet_data = {
        "id": auto,
        "timestamp": now,
        "sport": "...",
        "type": "Straight/Parlay",
        "odds": -110,
        "stake": 50,
        "to_win": 45.45,
        "payout": 95.45,
        "legs": [ {player, prop, type, line, ou} ],
        "result": "Pending/Won/Lost/Pushed",
    }
    """
    db = _load()

    new_id = 1
    if db["bets"]:
        new_id = max(b["id"] for b in db["bets"]) + 1

    bet_data["id"] = new_id
    bet_data["timestamp"] = datetime.now().isoformat()

    db["bets"].append(bet_data)
    _save(db)

    return new_id


def delete_bet(bet_id: int):
    """Remove bet by ID."""
    db = _load()
    db["bets"] = [b for b in db["bets"] if b["id"] != bet_id]
    _save(db)


def update_bet(bet_id: int, updated_fields: dict):
    """Update any fields in a bet."""
    db = _load()
    for bet in db["bets"]:
        if bet["id"] == bet_id:
            bet.update(updated_fields)
            break
    _save(db)


def reset_all_bets():
    """Wipe everything."""
    _save({"bets": []})

