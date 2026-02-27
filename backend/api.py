"""
api.py — ktdash.app integration
Single endpoint: GET https://ktdash.app/api/killteams?full=Y
"""

import json
import os
import requests
import streamlit as st

BASE_URL = "https://ktdash.app/api"
HEADERS  = {"Accept": "application/json"}
TIMEOUT  = 15

ABILITY_KEYWORD_MAP = {
    "medic":  ["medic", "heal", "patch up", "stimm"],
    "revive": ["revive", "recover", "bring back"],
    "comms":  ["comms", "signal", "relay", "vox"],
    "aura":   ["aura", "nearby", "within", "friendly operatives"],
    "buff":   ["add 1", "improve", "bonus", "enhance", "+1"],
}


DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "killteams.json")


def _raw_fetch() -> list[dict]:
    """Read from local data file if available, fall back to network."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Network fallback — run update_data.py to cache locally
    resp = requests.get(
        f"{BASE_URL}/killteams",
        headers=HEADERS,
        timeout=TIMEOUT,
        params={"full": "Y"},
    )
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=300, show_spinner="Loading kill teams from ktdash.app…")
def fetch_all_killteams() -> list[dict]:
    return _raw_fetch()


def fetch_killteam_names() -> list[str]:
    data = fetch_all_killteams()
    return sorted(kt["killteamName"] for kt in data if kt.get("killteamName"))


def fetch_roster(killteam_name: str) -> list[dict]:
    data = fetch_all_killteams()
    for kt in data:
        if kt.get("killteamName") != killteam_name:
            continue
        ops = []
        for op in kt.get("opTypes", []):
            mapped = _map_operative(op)
            if mapped:
                ops.append(mapped)
        return ops
    return []


# ── Mapping ───────────────────────────────────────────────────────────────────

def _map_operative(raw: dict) -> dict | None:
    try:
        move   = _parse_stat(raw.get("MOVE",   "6"))
        apl    = _parse_stat(raw.get("APL",    "2"))
        save   = _parse_stat(raw.get("SAVE",   "5+"))
        wounds = _parse_stat(raw.get("WOUNDS", "8"))

        keywords  = raw.get("keywords", "") or ""
        is_leader = "LEADER" in keywords.upper()

        weapons = []
        for w in raw.get("weapons", []) or []:
            wep_type_code = w.get("wepType", "M")
            if wep_type_code == "E":
                continue
            internal_type = "ranged" if wep_type_code in ("R", "P") else "melee"
            wep_name = w.get("wepName", "Unknown")

            for profile in w.get("profiles", []) or []:
                profile_name = profile.get("profileName", "")
                full_name    = f"{wep_name} ({profile_name})" if profile_name else wep_name
                dmg_raw      = str(profile.get("DMG", "3/4"))
                weapons.append({
                    "name":         full_name,
                    "type":         internal_type,
                    "attacks":      _parse_stat(profile.get("ATK", "3")),
                    "hit":          _parse_hit(profile.get("HIT",  "4+")),
                    "damage":       _parse_dmg_normal(dmg_raw),
                    "damage_crit":  _parse_dmg_crit(dmg_raw),
                    "rules":        profile.get("WR", "") or "",
                })

        raw_abilities  = raw.get("abilities", []) or []
        ability_tags   = _extract_ability_tags(raw_abilities)
        ability_names  = [a.get("abilityName", "") for a in raw_abilities if a.get("abilityName")]

        return {
            "name":          raw.get("opTypeName") or raw.get("opName") or "Unknown",
            "leader":        is_leader,
            "move":          move,
            "apl":           apl,
            "defense":       3,
            "save":          save,
            "wounds":        wounds,
            "abilities":     ability_tags,
            "ability_names": ability_names,
            "keywords":      keywords,
            "weapons":       weapons,
        }
    except Exception as e:
        return None


# ── Parsers ───────────────────────────────────────────────────────────────────

def _parse_stat(val) -> int:
    if isinstance(val, int):
        return val
    try:
        return int(str(val).replace('"', "").replace('"', "").replace("+", "").strip())
    except (ValueError, AttributeError):
        return 0


def _parse_hit(val: str) -> int:
    try:
        return int(str(val).replace("+", "").strip())
    except (ValueError, AttributeError):
        return 4


def _parse_dmg_normal(val: str) -> int:
    try:
        return int(str(val).split("/")[0].strip())
    except (ValueError, AttributeError, IndexError):
        return 3


def _parse_dmg_crit(val: str) -> int:
    try:
        parts = str(val).split("/")
        return int(parts[1].strip()) if len(parts) > 1 else int(parts[0].strip()) + 1
    except (ValueError, AttributeError, IndexError):
        return 4


def _extract_ability_tags(abilities: list) -> list[str]:
    tags = set()
    for ability in abilities:
        text = (
            (ability.get("abilityName") or "") + " " +
            (ability.get("description")  or "")
        ).lower()
        for tag, keywords in ABILITY_KEYWORD_MAP.items():
            if any(kw in text for kw in keywords):
                tags.add(tag)
    return list(tags)


# ── Debug ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from collections import Counter
    data = _raw_fetch()

    wr_tokens = Counter()
    for kt in data:
        for op in kt.get("opTypes", []):
            for w in op.get("weapons", []):
                for p in w.get("profiles", []):
                    wr = p.get("WR", "") or ""
                    for token in wr.split(","):
                        token = token.strip()
                        if token:
                            wr_tokens[token] += 1

    print(f"Total unique WR tokens: {len(wr_tokens)}\n")
    for token, count in sorted(wr_tokens.items(), key=lambda x: -x[1]):
        print(f"  {count:>4}x  {token}")
