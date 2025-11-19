def american_to_decimal(odds):
    odds = float(odds)
    if odds > 0:
        return (odds / 100) + 1
    return (100 / abs(odds)) + 1


def american_to_implied_prob(odds):
    odds = float(odds)
    if odds > 0:
        return 100 / (odds + 100)
    return abs(odds) / (abs(odds) + 100)


def calculate_to_win_and_payout(odds, stake):
    odds = float(odds)
    stake = float(stake)

    if odds > 0:
        to_win = stake * (odds / 100)
    else:
        to_win = stake / (abs(odds) / 100)

    payout = stake + to_win
    return round(to_win, 2), round(payout, 2)


def calculate_parlay_odds(legs):
    total_decimal = 1
    for o in legs:
        total_decimal *= american_to_decimal(o)
    parlay_decimal = total_decimal
    if parlay_decimal - 1 == 0:
        return 0
    if parlay_decimal >= 2:
        return int((parlay_decimal - 1) * 100)
    return int(-100 / (parlay_decimal - 1))


def calculate_kelly(bankroll, odds):
    p = american_to_implied_prob(odds)
    b = american_to_decimal(odds) - 1
    kelly_fraction = ((b * p) - (1 - p)) / b
    if kelly_fraction < 0:
        kelly_fraction = 0
    stake = round(bankroll * kelly_fraction, 2)
    return round(kelly_fraction, 4), stake
