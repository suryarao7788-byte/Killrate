"""
elo.py
------
Dual ELO system:

  Player ELO  — weighted against the faction used.
                Winning with strong teams gives diminishing returns.
                K-factor scales with faction weakness.

  Faction ELO — baseline set by PPO win rate (if available), else CYRAC rank.
                Higher real-world win rate → higher starting ELO.
                Strong teams gain slowly, weak teams gain quickly.

Faction baseline:
  PPO win rate 60%+ → ~1400
  PPO win rate 50%  → ~1200 (neutral)
  PPO win rate 40%- → ~1000
  Falls back to CYRAC rank interpolation if PPO data unavailable.
"""

from team_meta import CYRAC_RANK, CYRAC_TOTAL, get_ppo_winrate, _canonical, _resolve_cyrac

BASE_K               = 32
STARTING_PLAYER_ELO  = 1200
PROVISIONAL_GAMES    = 10


# ── Faction baseline ELO ──────────────────────────────────────────────────────

def faction_baseline(team_name: str) -> float:
    """
    Set baseline from PPO win rate if available.
    win rate 60% → 1400, 50% → 1200, 40% → 1000.
    Linear: ELO = 1200 + (winrate - 0.50) * 4000
    Falls back to CYRAC rank if no PPO data.
    """
    wr = get_ppo_winrate(_canonical(team_name))
    if wr is not None:
        # wr is already 0-100 from scraper, convert to 0-1
        wr_frac = wr / 100.0
        # 50% win rate = 1200, each 1% = 20 ELO points
        return round(1200 + (wr_frac - 0.50) * 4000, 1)

    # Fallback: CYRAC rank interpolation
    rank = CYRAC_RANK.get(_resolve_cyrac(team_name))
    if rank is None:
        return 1200
    return round(1400 - ((rank - 1) / max(CYRAC_TOTAL - 1, 1)) * 400, 1)


def _strength_percentile(team_name: str) -> float:
    """
    0.0 = strongest team, 1.0 = weakest.
    Uses PPO win rate if available, else CYRAC rank.
    """
    wr = get_ppo_winrate(_canonical(team_name))
    if wr is not None:
        # Higher win rate = lower percentile (stronger)
        # Clamp win rate to reasonable range 35-65%
        clamped = max(35.0, min(65.0, wr))
        return (65.0 - clamped) / 30.0   # 65% → 0.0, 35% → 1.0

    rank = CYRAC_RANK.get(_resolve_cyrac(team_name))
    if rank is None:
        return 0.5
    return (rank - 1) / max(CYRAC_TOTAL - 1, 1)


# ── K-factor scaling ──────────────────────────────────────────────────────────

def player_k(team_name: str) -> float:
    """
    Player gains less ELO when winning with strong teams.
    Strongest → K=16, Weakest → K=48
    """
    p = _strength_percentile(team_name)
    return BASE_K * (0.5 + p)   # 16 → 48


def faction_k(team_name: str) -> float:
    """
    Strong teams: losses matter more (K=48).
    Weak teams: losses matter less (K=16).
    """
    p = _strength_percentile(team_name)
    return BASE_K * (1.5 - p)   # 48 → 16


# ── Core ELO formula ──────────────────────────────────────────────────────────

def expected_score(my_elo: float, opp_elo: float) -> float:
    return 1 / (1 + 10 ** ((opp_elo - my_elo) / 400))


def outcome_value(outcome: str) -> float:
    return {"W": 1.0, "D": 0.5, "L": 0.0}[outcome]


# ── Player ELO ────────────────────────────────────────────────────────────────

def calc_player_elo(my_elo, opp_elo, outcome, my_team):
    k        = player_k(my_team)
    actual   = outcome_value(outcome)
    expected = expected_score(my_elo, opp_elo)
    change   = round(k * (actual - expected), 2)
    return round(my_elo + change, 2), change


# ── Faction ELO ───────────────────────────────────────────────────────────────

def calc_faction_elo(faction_elo, opp_faction_elo, outcome, team_name):
    k        = faction_k(team_name)
    actual   = outcome_value(outcome)
    expected = expected_score(faction_elo, opp_faction_elo)
    change   = round(k * (actual - expected), 2)
    return round(faction_elo + change, 2), change


# ── Provisional ───────────────────────────────────────────────────────────────

def is_provisional(games_played: int) -> bool:
    return games_played < PROVISIONAL_GAMES
