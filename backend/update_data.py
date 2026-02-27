"""
update_data.py
--------------
Fetches the full ktdash dataset and saves it locally.
Run this manually whenever GW releases a new kill team or FAQ update.

Usage:
    python update_data.py
"""

import json
import os
import requests
from datetime import datetime

DATA_DIR  = os.path.join(os.path.dirname(__file__), "data")
DATA_FILE = os.path.join(DATA_DIR, "killteams.json")

def update():
    print("Fetching from ktdash.app...")
    resp = requests.get(
        "https://ktdash.app/api/killteams",
        params={"full": "Y"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    os.makedirs(DATA_DIR, exist_ok=True)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    teams = [kt.get("killteamName") for kt in data if kt.get("killteamName")]
    print(f"Saved {len(teams)} kill teams to {DATA_FILE}")
    print(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("\nTeams saved:")
    for t in sorted(teams):
        print(f"  {t}")

if __name__ == "__main__":
    update()
