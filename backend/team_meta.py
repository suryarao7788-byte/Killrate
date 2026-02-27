"""
team_meta.py
------------
Community and expert metadata for each kill team.

Sources:
  - CYRAC Tier List (Can You Roll A Crit) — expert competitive ranking
  - Size Style / Play Style / Tricksy Level — from KT_Ranker_notes.xlsx
"""

# ── CYRAC Tier List ───────────────────────────────────────────────────────────
# Rank 1 = best. Based on CYRAC's published tier list.

CYRAC_RANK: dict[str, int] = {
    "Hierotek Circle":        1,
    "Sanctifiers":            2,
    "Wolf Scouts":            3,
    "Battleclade":            4,
    "Inquisitorial Agents":   5,
    "Brood Brothers":         6,
    "XV26 Stealth Battlesuits": 7,
    "Canoptek Circle":        8,
    "Murderwing":             9,
    "Nemesis Claw":           10,
    "Exaction Squad":         11,
    "Pathfinders":            12,
    "Hearthkyn Salvagers":    13,
    "Imperial Navy Breachers": 14,
    "Mandrakes":              15,
    "Death Korps":            16,
    "Farstalker Kinband":     17,
    "Hunter Clade":           18,
    "Deathwatch":             19,
    "Celestian Insidiants":   20,
    "Scout Squad":            21,
    "Kasrkin":                22,
    "Warp Coven":             23,
    "Corsair Voidscarred":    24,
    "Elucidian Starstriders": 25,
    "Angels Of Death":        26,
    "Ratlings":               27,
    "Hand Of The Archon":     28,
    "Plague Marines":         29,
    "Vespid Stingwings":      30,
    "Blades Of Khaine":       31,
    "Phobos Strike Team":     32,
    "Novitiates":             33,
    "Wrecka Krew":            34,
    "Wyrmblade":              35,
    "Void-Dancer Troupe":     36,
    "Gellerpox Infected":     37,
    "Hernkyn Yaegirs":        38,
    "Legionaries":            39,
    "Chaos Cult":             40,
    "Raveners":               41,
    "Blooded":                42,
    "Kommandos":              43,
    "Fellgor Ravagers":       44,
    "Tempestus Aquilon":      45,
    "Goremongers":            46,
}

CYRAC_TOTAL = len(CYRAC_RANK)

# ── Team characteristics ──────────────────────────────────────────────────────
# size_style:  Horde | Elite | Hyper-elite | Midrange | Mixed
# play_style:  Ranged | Melee | Assault | Mixed | Variable
# tricksy:     Low | Mod | High | None

TEAM_META: dict[str, dict] = {
    "Hierotek Circle":        {"size": "Elite",       "play": "Ranged",   "tricksy": None},
    "Sanctifiers":            {"size": "Horde",       "play": "Melee",    "tricksy": None},
    "Wolf Scouts":            {"size": "Hyper-elite", "play": "Mixed",    "tricksy": None},
    "Battleclade":            {"size": "Horde",       "play": "Mixed",    "tricksy": "Mod"},
    "Inquisitorial Agents":   {"size": "Horde",       "play": "Variable", "tricksy": "Mod"},
    "Brood Brothers":         {"size": "Horde",       "play": "Mixed",    "tricksy": None},
    "XV26 Stealth Battlesuits": {"size": "Hyper-elite", "play": "Ranged", "tricksy": "Mod"},
    "Canoptek Circle":        {"size": "Hyper-elite", "play": "Ranged",   "tricksy": None},
    "Murderwing":             {"size": "Elite",       "play": "Melee",    "tricksy": None},
    "Nemesis Claw":           {"size": "Elite",       "play": "Melee",    "tricksy": None},
    "Exaction Squad":         {"size": "Horde",       "play": "Assault",  "tricksy": None},
    "Pathfinders":            {"size": "Horde",       "play": "Ranged",   "tricksy": "Mod"},
    "Hearthkyn Salvagers":    {"size": "Horde",       "play": "Ranged",   "tricksy": None},
    "Imperial Navy Breachers": {"size": "Horde",      "play": "Assault",  "tricksy": None},
    "Mandrakes":              {"size": "Midrange",    "play": "Melee",    "tricksy": "High"},
    "Death Korps":            {"size": "Horde",       "play": "Ranged",   "tricksy": "Low"},
    "Farstalker Kinband":     {"size": "Horde",       "play": "Mixed",    "tricksy": None},
    "Hunter Clade":           {"size": "Horde",       "play": "Ranged",   "tricksy": None},
    "Deathwatch":             {"size": "Hyper-elite", "play": "Mixed",    "tricksy": None},
    "Celestian Insidiants":   {"size": "Horde",       "play": "Mixed",    "tricksy": None},
    "Scout Squad":            {"size": "Horde",       "play": "Ranged",   "tricksy": "High"},
    "Kasrkin":                {"size": "Horde",       "play": "Ranged",   "tricksy": None},
    "Warp Coven":             {"size": "Mixed",       "play": "Mixed",    "tricksy": "High"},
    "Corsair Voidscarred":    {"size": "Midrange",    "play": "Mixed",    "tricksy": "High"},
    "Elucidian Starstriders": {"size": "Horde",       "play": "Ranged",   "tricksy": "Mod"},
    "Angels Of Death":        {"size": "Elite",       "play": "Variable", "tricksy": None},
    "Ratlings":               {"size": "Mixed",       "play": "Variable", "tricksy": "High"},
    "Hand Of The Archon":     {"size": "Midrange",    "play": "Mixed",    "tricksy": "Mod"},
    "Plague Marines":         {"size": "Elite",       "play": "Mixed",    "tricksy": None},
    "Vespid Stingwings":      {"size": "Midrange",    "play": "Ranged",   "tricksy": "Mod"},
    "Blades Of Khaine":       {"size": "Midrange",    "play": "Variable", "tricksy": "High"},
    "Phobos Strike Team":     {"size": "Elite",       "play": "Variable", "tricksy": "High"},
    "Novitiates":             {"size": "Horde",       "play": "Melee",    "tricksy": "Mod"},
    "Wrecka Krew":            {"size": "Elite",       "play": "Variable", "tricksy": None},
    "Wyrmblade":              {"size": "Horde",       "play": "Ranged",   "tricksy": None},
    "Void-Dancer Troupe":     {"size": "Midrange",    "play": "Melee",    "tricksy": "High"},
    "Gellerpox Infected":     {"size": "Horde",       "play": "Melee",    "tricksy": None},
    "Hernkyn Yaegirs":        {"size": "Midrange",    "play": "Assault",  "tricksy": None},
    "Legionaries":            {"size": "Elite",       "play": "Variable", "tricksy": None},
    "Chaos Cult":             {"size": "Mixed",       "play": "Variable", "tricksy": None},
    "Raveners":               {"size": "Hyper-elite", "play": "Melee",    "tricksy": "Mod"},
    "Blooded":                {"size": "Horde",       "play": "Mixed",    "tricksy": None},
    "Kommandos":              {"size": "Midrange",    "play": "Mixed",    "tricksy": "Mod"},
    "Fellgor Ravagers":       {"size": "Horde",       "play": "Melee",    "tricksy": None},
    "Tempestus Aquilon":      {"size": "Horde",       "play": "Ranged",   "tricksy": None},
    "Goremongers":            {"size": "Horde",       "play": "Melee",    "tricksy": None},
}

# ── Display helpers ───────────────────────────────────────────────────────────

SIZE_COLORS = {
    "Horde":       "#22c55e",
    "Midrange":    "#3b82f6",
    "Elite":       "#f59e0b",
    "Hyper-elite": "#ef4444",
    "Mixed":       "#8b5cf6",
}

PLAY_COLORS = {
    "Ranged":   "#3b82f6",
    "Melee":    "#ef4444",
    "Assault":  "#f59e0b",
    "Mixed":    "#8b5cf6",
    "Variable": "#6b7280",
}

TRICKSY_COLORS = {
    "Low":  "#22c55e",
    "Mod":  "#f59e0b",
    "High": "#ef4444",
}

TRICKSY_ICONS = {
    "Low":  "🎲",
    "Mod":  "🎲🎲",
    "High": "🎲🎲🎲",
}


def get_cyrac_rank(team_name: str) -> int | None:
    return CYRAC_RANK.get(team_name)




def get_meta(team_name: str) -> dict:
    return TEAM_META.get(team_name, {"size": None, "play": None, "tricksy": None})


def meta_badges_html(team_name: str) -> str:
    meta = get_meta(team_name)
    badges = []

    def badge(label, color):
        return (
            f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
            f'font-size:11px;font-weight:600;background:{color}22;color:{color};'
            f'border:1px solid {color}44;margin:1px">{label}</span>'
        )

    if meta.get("size"):
        badges.append(badge(meta["size"], SIZE_COLORS.get(meta["size"], "#888")))
    if meta.get("play"):
        badges.append(badge(meta["play"], PLAY_COLORS.get(meta["play"], "#888")))
    if meta.get("tricksy"):
        t = meta["tricksy"]
        badges.append(badge(f"{TRICKSY_ICONS[t]} {t} Tricksy", TRICKSY_COLORS.get(t, "#888")))

    return " ".join(badges)


def cyrac_badge_html(team_name: str) -> str:
    rank  = CYRAC_RANK.get(team_name)
    tier  = get_cyrac_tier(team_name)
    if rank is None:
        return ""
    tier_colors = {"S": "#f59e0b", "A": "#22c55e", "B": "#3b82f6", "C": "#8b5cf6", "D": "#6b7280"}
    color = tier_colors.get(tier, "#888")
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:10px;'
        f'font-size:11px;font-weight:600;background:{color}22;color:{color};'
        f'border:1px solid {color}44;margin:1px">CYRAC #{rank} ({tier}-Tier)</span>'
    )


# ── Dynamic CYRAC loading ─────────────────────────────────────────────────────
# Loads from scraped JSON if available, otherwise falls back to CYRAC_RANK above.

import os as _os
import json as _json

_CYRAC_JSON = _os.path.join(_os.path.dirname(__file__), "data", "cyrac_tiers.json")

def _load_dynamic_cyrac() -> dict | None:
    if _os.path.exists(_CYRAC_JSON):
        with open(_CYRAC_JSON) as f:
            return _json.load(f)
    return None

_dynamic = _load_dynamic_cyrac()

if _dynamic:
    # Override static CYRAC_RANK with scraped data
    _teams = _dynamic.get("teams", {})
    CYRAC_RANK = {name: d["global_rank"] for name, d in _teams.items()}
    CYRAC_TIER_MAP = {name: d["tier"] for name, d in _teams.items()}
    CYRAC_SCRAPED_AT = _dynamic.get("scraped_at", "unknown")
    CYRAC_SOURCE_URL = _dynamic.get("url", "")
    CYRAC_TOTAL = len(CYRAC_RANK)
else:
    CYRAC_TIER_MAP = {}
    CYRAC_SCRAPED_AT = None
    CYRAC_SOURCE_URL = None


def get_cyrac_tier(team_name: str) -> str:
    # Use scraped tier map if available (more accurate than rank-based bucketing)
    if CYRAC_TIER_MAP and team_name in CYRAC_TIER_MAP:
        return CYRAC_TIER_MAP[team_name]
    # Fall back to rank-based calculation
    rank = CYRAC_RANK.get(team_name)
    if rank is None:
        return "Unranked"
    pct = rank / CYRAC_TOTAL
    if pct <= 0.10: return "S"
    if pct <= 0.25: return "A"
    if pct <= 0.50: return "B"
    if pct <= 0.75: return "C"
    return "D"
