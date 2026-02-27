# paste into a file called debug_scrape.py
import requests, re

url = "https://canyourollacrit.com/2026/02/11/kill-team-tier-list-q1-2026/"
headers = {"User-Agent": "Mozilla/5.0"}
r = requests.get(url, headers=headers, timeout=15)
html = r.text

# Show what's around "S Tier"
idx = html.find("S Tier")
print("=== Around 'S Tier' ===")
print(repr(html[max(0,idx-200):idx+300]))
print()

# Show what's around "Fellgor"
idx2 = html.find("Fellgor")
print("=== Around 'Fellgor' ===")
print(repr(html[max(0,idx2-100):idx2+200]))
