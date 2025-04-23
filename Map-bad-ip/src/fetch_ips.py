#!/usr/bin/env python3
"""
fetch_ips.py
Récupère un flux RSS d’IP malveillantes, extrait les adresses IP et les stocke
dans data/ips.csv et data/ips.json (uniquement les nouvelles).
"""

import os
import re
import json
import feedparser
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

FEED_URL = os.getenv("RSS_FEED_URL", "https://raw.githubusercontent.com/duggytuxy/Intelligence_IPv4_Blocklists/refs/heads/main/agressive_ips_dst_fr_be_blocklist.txt")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "ips.csv")
JSON_PATH = os.path.join(DATA_DIR, "ips.json")

IP_REGEX = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")

def load_existing():
    if os.path.exists(CSV_PATH):
        return set(pd.read_csv(CSV_PATH, header=None)[0].astype(str))
    return set()

def save(ips_set):
    os.makedirs(DATA_DIR, exist_ok=True)
    # CSV
    pd.Series(sorted(ips_set)).to_csv(CSV_PATH, index=False, header=False)
    # JSON
    with open(JSON_PATH, "w") as f:
        json.dump(sorted(ips_set), f, indent=2)

def fetch():
    feed = feedparser.parse(FEED_URL)
    found = set()
    for entry in feed.entries:
        text = entry.get("title", "") + " " + entry.get("description", "")
        for ip in IP_REGEX.findall(text):
            found.add(ip)
    return found

def main():
    existing = load_existing()
    new = fetch()
    all_ips = existing.union(new)
    save(all_ips)
    print(f"[+] Total IPs stored: {len(all_ips)}")

if __name__ == "__main__":
    main()
