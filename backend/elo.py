"""
elo.py
------
Dual ELO system:

  Player ELO  — weighted against the faction used.
                Winning with strong teams (low CYRAC rank) gives diminishing returns.
                K-factor scales with faction weakness — playing rank 46 gains faster.

  Faction ELO — inversely weighted against winrate.
                Strong teams start high but gain slowly.
                Weak teams start low but gain quickly.
                Opponent is always the faction being played against.
"""

from team_meta import CYRAC_RANK, CYRAC_TOTAL

BASE_K          = 32
STARTING_PLAYER_ELO  = 1200
PROVISIONAL_GAMES    = 10   # below this, rating shown as provisional


# ── Faction baseline ELO ──────────────────────────────────────────────────────
# Rank 1  → 1400 (strongest, hardest to improve)
# Rank 46 → 1000 (weakest, easiest to improve)

def faction_baseline(team_name: str) -> float:
    rank = CYRAC_RANK.get(team_name)
    if rank is None:
        return 1200  # unknown team — neutral baseline
    # Linear interpolation: rank 1 = 1400, rank N = 1000
    return 1400 - ((rank - 1) / max(CYRAC_TOTAL - 1, 1)) * 400


# ── K-factor scaling ──────────────────────────────────────────────────────────

def player_k(team_name: str) -> float:
    """
    Player gains less ELO when winning with strong teams.
    rank 1  (best)  → K = 16   (slow gain)
    rank 46 (worst) → K = 48   (fast gain)
    """
    rank = CYRAC_RANK.get(team_name)
    if rank is None:
        return BASE_K
    percentile = (rank - 1) / max(CYRAC_TOTAL - 1, 1)  # 0=best, 1=worst
    return BASE_K * (0.5 + percentile)                  # 16 → 48


def faction_k(team_name: str) -> float:
    """
    Faction ELO changes faster for weak teams than strong ones.
    rank 1  (best)  → K = 48   (loses matter more — you're expected to win)
    rank 46 (worst) → K = 16   (losses matter less — upsets are expected)
    """
    rank = CYRAC_RANK.get(team_name)
    if rank is None:
        return BASE_K
    percentile = (rank - 1) / max(CYRAC_TOTAL - 1, 1)
    return BASE_K * (1.5 - percentile)                  # 48 → 16


# ── Core ELO formula ─────────────────────────────────────────────────────────

def expected_score(my_elo: float, opp_elo: float) -> float:
    return 1 / (1 + 10 ** ((opp_elo - my_elo) / 400))


def outcome_value(outcome: str) -> float:
    return {"W": 1.0, "D": 0.5, "L": 0.0}[outcome]


# ── Player ELO calculation ────────────────────────────────────────────────────

def calc_player_elo(
    my_elo: float,
    opp_elo: float,
    outcome: str,
    my_team: str,
) -> tuple[float, float]:
    """
    Returns (new_elo, change).
    K-factor penalises wins with strong teams.
    """
    k        = player_k(my_team)
    actual   = outcome_value(outcome)
    expected = expected_score(my_elo, opp_elo)
    change   = round(k * (actual - expected), 2)
    return round(my_elo + change, 2), change


# ── Faction ELO calculation ───────────────────────────────────────────────────

def calc_faction_elo(
    faction_elo: float,
    opp_faction_elo: float,
    outcome: str,
    team_name: str,
) -> tuple[float, float]:
    """
    Returns (new_faction_elo, change).
    K-factor is inverse — strong teams gain less from wins.
    """
    k        = faction_k(team_name)
    actual   = outcome_value(outcome)
    expected = expected_score(faction_elo, opp_faction_elo)
    change   = round(k * (actual - expected), 2)
    return round(faction_elo + change, 2), change


# ── Provisional flag ──────────────────────────────────────────────────────────

def is_provisional(games_played: int) -> bool:
    return games_played < PROVISIONAL_GAMES
