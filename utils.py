import math


# --------------------------------------------------------
# AMERICAN ODDS CONVERSION
# --------------------------------------------------------

def american_to_decimal(odds: int) -> float:
    """Convert American odds to decimal odds."""
    if odds > 0:
        return 1 + (odds / 100)
    else:
        return 1 + (100 / abs(odds))


def decimal_to_american(decimal_odds: float) -> int:
    """Convert decimal odds back to American odds."""
    if decimal_odds >= 2.0:
        return int((decimal_odds - 1) * 100)
    else:
        return int(-100 / (decimal_odds - 1))


# --------------------------------------------------------
# IMPLIED PROBABILITY
# --------------------------------------------------------

def implied_probability(odds: int) -> float:
    """Return the implied win probability (0-1)."""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


# --------------------------------------------------------
# KELLY CRITERION
# --------------------------------------------------------

def kelly_stake(bankroll: float, win_prob: float, odds: int) -> float:
    """Calculate the optimal Kelly stake amount."""
    dec = american_to_decimal(odds)
    edge = (dec * win_prob) - 1

    if dec <= 1 or edge <= 0:
        return 0

    kelly_fraction = (edge / (dec - 1))

    if kelly_fraction < 0:
        return 0

    return bankroll * kelly_fraction


def kelly_half(bankroll: float, win_prob: float, odds: int) -> float:
    return kelly_stake(bankroll, win_prob, odds) / 2


def kelly_quarter(bankroll: float, win_prob: float, odds: int) -> float:
    return kelly_stake(bankroll, win_prob, odds) / 4


# --------------------------------------------------------
# EXPECTED VALUE (EV)
# --------------------------------------------------------

def expected_value(stake: float, odds: int, win_prob: float) -> float:
    """Calculate +EV or -EV dollar value."""
    dec = american_to_decimal(odds)
    lose_prob = 1 - win_prob
    win_return = stake * (dec - 1)
    lose_return = -stake
    return (win_prob * win_return) + (lose_prob * lose_return)


# --------------------------------------------------------
# PAYOUT CALCULATIONS (FanDuel-style)
# --------------------------------------------------------

def calculate_to_win(stake: float, odds: int) -> float:
    """Calculate 'To Win' amount from stake + American odds."""
    if odds > 0:
        return round(stake * (odds / 100), 2)
    else:
        return round(stake * (100 / abs(odds)), 2)


def calculate_payout(stake: float, odds: int) -> float:
    """Total return including stake."""
    return round(stake + calculate_to_win(stake, odds), 2)


# --------------------------------------------------------
# PARLAY MATH (FanDuel)
# --------------------------------------------------------

def parlay_to_win(stake: float, final_odds: int) -> float:
    """FanDuel-style parlay payout."""
    return calculate_to_win(stake, final_odds)


def parlay_payout(stake: float, final_odds: int) -> float:
    return calculate_payout(stake, final_odds)


# --------------------------------------------------------
# UNIT HELPER
# --------------------------------------------------------

def units_won(profit: float, unit_size: float) -> float:
    """Convert profit dollars to units."""
    if unit_size <= 0:
        return 0
    return round(profit / unit_size, 2)
