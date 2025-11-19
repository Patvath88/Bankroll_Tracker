import json
import os
from typing import List, Dict, Any

STORAGE_FILE = "bets.json"


def load_bets() -> List[Dict[str, Any]]:
    """Load all bets from persistent storage."""
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []


def save_bets(bets: List[Dict[str, Any]]) -> None:
    """Save bets to persistent JSON storage."""
    with open(STORAGE_FILE, "w") as f:
        json.dump(bets, f, indent=4)


def add_bet(bet: Dict[str, Any]) -> None:
    """Add a new bet to storage."""
    bets = load_bets()
    bets.append(bet)
    save_bets(bets)


def update_bet(index: int, updated_bet: Dict[str, Any]) -> None:
    """Edit an existing bet."""
    bets = load_bets()
    if 0 <= index < len(bets):
        bets[index] = updated_bet
        save_bets(bets)


def delete_bet(index: int) -> None:
    """Delete a bet by index."""
    bets = load_bets()
    if 0 <= index < len(bets):
        bets.pop(index)
        save_bets(bets)
