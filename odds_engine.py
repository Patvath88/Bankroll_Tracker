import math


# ------------------------------------------------------------------------------
# AMERICAN ODDS → IMPLIED PROBABILITY
# ------------------------------------------------------------------------------

def american_to_implied_prob(odds: float) -> float:
    """Convert American odds to implied probability (0 to 1)."""
    try:
        odds = float(odds)
    except:
        return 0.0

    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)


# ------------------------------------------------------------------------------
# IMPLIED PROBABILITY → AMERICAN ODDS
# ------------------------------------------------------------------------------

def implied_prob_to_american(p: float) -> float:
    """Convert implied probability back to American odds."""
    if p <= 0:
        return 0
    if p >= 1:
        return -1000000
    if p > 0.5:
        return -100 * (p / (1 - p))
    return (100 * (1 - p)) / p


# ------------------------------------------------------------------------------
# AMERICAN ODDS → DECIMAL
# ------------------------------------------------------------------------------

def american_to_decimal(odds: float) -> float:
    """American odds to decimal odds."""
    odds = float(odds)
    if odds > 0:
        return (odds / 100) + 1
    else:
        return (100 / -odds) + 1


# ------------------------------------------------------------------------------
# DECIMAL ODDS → AMERICAN
# ------------------------------------------------------------------------------

def decimal_to_american(decimal_odds: float) -> float:
    """Convert decimal odds back to American odds."""
    if decimal_odds >= 2:
        return (decimal_odds - 1) * 100
    else:
        return -100 / (decimal_odds - 1)


# ------------------------------------------------------------------------------
# PARLAY ODDS (MULTIPLY DECIMALS)
# ------------------------------------------------------------------------------

def calculate_parlay_odds(legs):
    """
    legs = [
        {"odds": -110}, {"odds": 250}, ...
    ]

    We treat each leg using implied prob → decimal → multiply.
    """

    total_decimal = 1.0

    for leg in legs:
        odds = leg.get("odds")
        if odds is None or odds == "":
            # Skip legs with no odds (FD sometimes hides)
            continue
        try:
            d = american_to_decimal(float(odds))
            total_decimal *= d
        except:
            continue

    # Convert back to American style
    parlay_american = decimal_to_american(total_decimal)
    return round(parlay_american)


# ------------------------------------------------------------------------------
# PAYOUT CALCULATIONS
# ------------------------------------------------------------------------------

def calculate_to_win_and_payout(odds: float, stake: float):
    """
    Given American odds and a stake, calculate:
    - To Win amount
    - Total Payout (stake + win)
    """

    decimal_odds = american_to_decimal(odds)
    to_win = (decimal_odds - 1) * stake
    payout = stake + to_win

    return round(to_win, 2), round(payout, 2)


# ------------------------------------------------------------------------------
# EXPECTED VALUE (EV)
# ------------------------------------------------------------------------------

def calculate_ev(stake: float, odds: float):
    """
    EV = (p * profit_if_win) – ((1 - p) * stake)
    p is implied probability from odds
    """

    p = american_to_implied_prob(odds)
    to_win, _ = calculate_to_win_and_payout(odds, stake)
    ev = (p * to_win) - ((1 - p) * stake)

    return round(ev, 2), p


# ------------------------------------------------------------------------------
# KELLY CRITERION
# ------------------------------------------------------------------------------

def calculate_kelly(bankroll: float, odds: float):
    """
    Kelly fraction:
    f* = (bp - q) / b
    b = decimal_odds - 1
    p = implied probability
    q = 1 - p
    """

    decimal_odds = american_to_decimal(odds)
    b = decimal_odds - 1
    p = american_to_implied_prob(odds)
    q = 1 - p

    try:
        kelly_fraction = (b * p - q) / b
    except ZeroDivisionError:
        return 0.0

    if kelly_fraction < 0:
        kelly_fraction = 0

    recommended_stake = bankroll * kelly_fraction

    return round(kelly_fraction, 4), round(recommended_stake, 2)
