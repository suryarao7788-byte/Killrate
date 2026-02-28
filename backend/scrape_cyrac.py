"""
scrape_cyrac.py
---------------
Scrapes the latest CYRAC Kill Team tier list from canyourollacrit.com.

HTML structure:
    <h2 id="s-tier"><strong>S Tier</strong></h2>
    <p>Fellgor Ravager: description...</p>
    <p>Canoptek Circle: description...</p>
    <h2 id="a-tier"><strong>A Tier</strong></h2>
    ...

Run manually each quarter:
    python scrape_cyrac.py

Saves to: data/cyrac_tiers.json
"""

import requests
import json
import re
import os
from datetime import datetime, timezone

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

TIER_LIST_URL = "https://canyourollacrit.com/2026/02/11/kill-team-tier-list-q1-2026/"
OUTPUT_FILE   = os.path.join(os.path.dirname(__file__), "data", "cyrac_tiers.json")
TIER_VALUES   = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}


def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.text


def strip_tags(html: str) -> str:
    return re.sub(r'<[^>]+>', '', html).strip()


def parse_tiers(html: str) -> dict[str, str]:
    results = {}

    # Split on h2 tier headings: <h2 id="s-tier">, <h2 id="a-tier"> etc.
    section_re = re.compile(
        r'<h2[^>]*id="([sabcd])-tier"[^>]*>.*?</h2>(.*?)(?=<h2|$)',
        re.DOTALL | re.IGNORECASE
    )

    for m in section_re.finditer(html):
        tier         = m.group(1).upper()
        section_html = m.group(2)

        # Each team is in a <p> tag: "Team Name: description"
        for p_match in re.finditer(r'<p[^>]*>(.*?)</p>', section_html, re.DOTALL):
            text = strip_tags(p_match.group(1)).strip()
            if ':' not in text:
                continue

            name = text.split(':')[0].strip()

            # Validity
            if len(name) < 4 or len(name) > 50:
                continue
            if not name[0].isupper():
                continue
            if re.search(r'[<>/@\[\]]', name):
                continue
            if any(skip in name.lower() for skip in [
                'tier', 'http', 'also', 'note', 'factions',
                'someone', 'this is', 'kill team'
            ]):
                continue

            if name not in results:
                results[name] = tier

    return results


def build_output(teams: dict[str, str], url: str) -> dict:
    global_rank = 1
    ranked      = {}
    for tier in ["S", "A", "B", "C", "D"]:
        for name, t in teams.items():
            if t == tier:
                ranked[name] = {
                    "tier":        tier,
                    "tier_value":  TIER_VALUES[tier],
                    "global_rank": global_rank,
                }
                global_rank += 1
    return {
        "source":      "CYRAC (Can You Roll A Crit?)",
        "url":         url,
        "scraped_at":  datetime.now(timezone.utc).isoformat(),
        "total_teams": len(ranked),
        "teams":       ranked,
    }


def scrape(url: str = TIER_LIST_URL) -> dict:
    print(f"  [CYRAC] Fetching tier list...")
    html  = fetch_html(url)
    print(f"  [CYRAC] HTML fetched ({len(html):,} bytes)")
    teams = parse_tiers(html)
    print(f"  [CYRAC] Parsed {len(teams)} teams")
    if len(teams) < 10:
        print("  WARNING: low count. Found:", list(teams.keys()))
    return build_output(teams, url)


def save(data: dict):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  [CYRAC] Saved to {OUTPUT_FILE}")


def load() -> dict | None:
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE) as f:
            return json.load(f)
    return None


def get_tier(team_name: str, data: dict | None = None) -> str:
    if data is None:
        data = load()
    if not data:
        return "C"
    teams = data.get("teams", {})
    if team_name in teams:
        return teams[team_name]["tier"]
    lower = {k.lower(): v for k, v in teams.items()}
    return lower.get(team_name.lower(), {}).get("tier", "C")


def get_rank(team_name: str, data: dict | None = None) -> int | None:
    if data is None:
        data = load()
    if not data:
        return None
    teams = data.get("teams", {})
    if team_name in teams:
        return teams[team_name]["global_rank"]
    lower = {k.lower(): v for k, v in teams.items()}
    entry = lower.get(team_name.lower())
    return entry["global_rank"] if entry else None




def refresh():
    """Fetch fresh data and save. Called on startup."""
    try:
        data = scrape()
        save(data)
        return data
    except Exception as e:
        print(f"  [CYRAC] WARNING: Could not fetch tier list: {e}")
        print(f"  [CYRAC] Using cached data if available.")
        return load()
if __name__ == "__main__":
    data = scrape()
    print("\nResults by tier:")
    for tier in ["S", "A", "B", "C", "D"]:
        names = [n for n, d in data["teams"].items() if d["tier"] == tier]
        if names:
            print(f"  {tier}: {', '.join(names)}")
    save(data)
    print("\nDone.")
