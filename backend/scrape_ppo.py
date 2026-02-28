"""
scrape_ppo.py
-------------
Fetches live rankings from Pretentious Plastic Ops API on startup.
Saves to data/ppo_rankings.json for use during the session.

Called automatically by main.py on startup — no manual intervention needed.
"""

import requests
import json
import os
from datetime import datetime, timezone

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

BASE_URL    = "https://www.pretentiousplasticops.com/api/stats/rankings"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "data", "ppo_rankings.json")

# Current quarter — update each quarter
YEAR   = 2026
PERIOD = 1  # 1=Q1, 2=Q2, 3=Q3, 4=Q4


def fetch_all(year: int = YEAR, period: int = PERIOD) -> list[dict]:
    """Fetch all teams — try increasing limits until we get everything."""
    for limit in [200, 100, 50]:
        url = f"{BASE_URL}?year={year}&period={period}&isGt=false&isClassified=false&limit={limit}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            r.raise_for_status()
            data = r.json()
            teams = data["teams"] if isinstance(data, dict) and "teams" in data else data
            if isinstance(teams, list) and teams:
                return teams
        except Exception:
            continue

    # Fallback — no limit param
    url = f"{BASE_URL}?year={year}&period={period}&isGt=false&isClassified=false"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data["teams"] if isinstance(data, dict) and "teams" in data else data


def parse(teams: list[dict], year: int, period: int) -> dict:
    result = {}
    for i, entry in enumerate(teams):
        name         = entry.get("teamName") or entry.get("name") or f"Unknown_{i}"
        win_stat     = entry.get("winStat")     or {}
        placing_stat = entry.get("placingStat") or {}
        sample_stat  = entry.get("sampleStat")  or {}

        win_rate     = win_stat.get("value")     or 0
        placing_rate = placing_stat.get("value") or 0
        picks        = sample_stat.get("picks")  or 0
        games        = sample_stat.get("games")  or 0
        tier_est     = entry.get("tierEst")      or 0
        ppo_tier     = (entry.get("tier") or {}).get("description", "")
        ppo_rank     = entry.get("rank") or (i + 1)

        wr = float(win_rate)
        pr = float(placing_rate)

        result[name] = {
            "rank":         ppo_rank,
            "win_rate":     round(wr * 100, 1) if wr <= 1 else round(wr, 1),
            "placing_rate": round(pr * 100, 1) if pr <= 1 else round(pr, 1),
            "picks":        picks,
            "games":        games,
            "tier_est":     round(float(tier_est), 4),
            "ppo_tier":     ppo_tier,
        }
    return result


def scrape(year: int = YEAR, period: int = PERIOD) -> dict:
    print(f"  [PPO] Fetching rankings Q{period} {year}...")
    teams = fetch_all(year, period)
    print(f"  [PPO] Got {len(teams)} teams")
    parsed = parse(teams, year, period)
    return {
        "source":      "Pretentious Plastic Ops (BCP tournament data)",
        "url":         BASE_URL,
        "quarter":     f"Q{period} {year}",
        "scraped_at":  datetime.now(timezone.utc).isoformat(),
        "total_teams": len(parsed),
        "teams":       parsed,
    }


def save(data: dict):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  [PPO] Saved {data['total_teams']} teams to {OUTPUT_FILE}")


def load() -> dict | None:
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return None


def refresh():
    """Fetch fresh data and save. Called on startup."""
    try:
        data = scrape()
        save(data)
        return data
    except Exception as e:
        print(f"  [PPO] WARNING: Could not fetch rankings: {e}")
        print(f"  [PPO] Using cached data if available.")
        return load()


def get_rank(team_name: str, data: dict | None = None) -> int | None:
    if data is None: data = load()
    if not data: return None
    teams = data.get("teams", {})
    if team_name in teams: return teams[team_name]["rank"]
    lower = {k.lower(): v for k, v in teams.items()}
    entry = lower.get(team_name.lower())
    return entry["rank"] if entry else None


def get_win_rate(team_name: str, data: dict | None = None) -> float | None:
    if data is None: data = load()
    if not data: return None
    teams = data.get("teams", {})
    if team_name in teams: return teams[team_name]["win_rate"]
    lower = {k.lower(): v for k, v in teams.items()}
    entry = lower.get(team_name.lower())
    return entry["win_rate"] if entry else None


if __name__ == "__main__":
    data = scrape()
    print("\nAll teams by rank:")
    for name, d in sorted(data["teams"].items(), key=lambda x: x[1]["rank"]):
        print(f"  {d['rank']:2}. {name:<35} {d['win_rate']}% win rate  ({d['games']} games)  PPO: {d['ppo_tier']}")
    save(data)
    print("\nDone.")
