#!/usr/bin/env python3
"""
fetch_ips.py
Récupère un fichier texte d’IP malveillantes, extrait les adresses IP et les stocke
dans data/ips.csv et data/ips.json.
"""

import os
import re
import json
import requests
import pandas as pd
from pandas.errors import EmptyDataError
from dotenv import load_dotenv

load_dotenv()

FEED_URL = os.getenv(
    "RSS_FEED_URL",
    "https://raw.githubusercontent.com/duggytuxy/Intelligence_IPv4_Blocklists/refs/heads/main/agressive_ips_dst_fr_be_blocklist.txt"
)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "ips.csv")
JSON_PATH = os.path.join(DATA_DIR, "ips.json")

IP_REGEX = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")

def load_existing():
    """
    Charge les IP déjà sauvegardées, ou retourne un set vide
    si le fichier n'existe pas ou est vide.
    """
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH, header=None)
            return set(df[0].astype(str))
        except EmptyDataError:
            return set()
    return set()

def save(ips_set):
    os.makedirs(DATA_DIR, exist_ok=True)
    # CSV
    pd.Series(sorted(ips_set)).to_csv(CSV_PATH, index=False, header=False)
    # JSON
    with open(JSON_PATH, "w") as f:
        json.dump(sorted(ips_set), f, indent=2)

def fetch():
    """
    Récupère le fichier texte brut et en extrait toutes les IP.
    """
    resp = requests.get(FEED_URL, timeout=10)
    resp.raise_for_status()
    return set(IP_REGEX.findall(resp.text))

def main():
    existing = load_existing()
    new = fetch()
    all_ips = existing.union(new)
    save(all_ips)
    print(f"[+] Total IPs stored: {len(all_ips)}")

if __name__ == "__main__":
    main()
