#!/usr/bin/env python3
"""
fetch_ips.py
Recupere un fichier texte d'IP malveillantes, extrait les adresses IP et stocke uniquement les nouvelles
adresses dans data/ips.csv et met a jour data/ips.json.
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
    "https://raw.githubusercontent.com/duggytuxy/Data-Shield_IPv4_Blocklist/refs/heads/main/prod_data-shield_ipv4_blocklist.txt"
)
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "ips.csv")
JSON_PATH = os.path.join(DATA_DIR, "ips.json")

IP_REGEX = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ClubCyber-ThreatFeed/1.0)",
    "Accept": "text/plain",
}


def load_existing():
    """
    Charge les IP deja sauvegardees, ou retourne un set vide si le fichier n'existe pas ou est vide.
    """
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH, header=None)
            return set(df[0].astype(str))
        except EmptyDataError:
            return set()
    return set()


def fetch():
    """
    Recupere le fichier texte brut et en extrait toutes les IP.
    """
    resp = requests.get(FEED_URL, timeout=15, headers=HEADERS)
    resp.raise_for_status()
    return set(IP_REGEX.findall(resp.text))


def save_all(ips_set):
    """
    Sauvegarde l'ensemble des IP dans ips.csv et ips.json.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    pd.Series(sorted(ips_set)).to_csv(CSV_PATH, index=False, header=False)
    with open(JSON_PATH, "w") as f:
        json.dump(sorted(ips_set), f, indent=2)


def save_new(new_ips, all_ips):
    """
    Ajoute uniquement les nouvelles IP a ips.csv (mode append) et met a jour ips.json.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    pd.Series(sorted(new_ips)).to_csv(CSV_PATH, index=False, header=False, mode="a")
    with open(JSON_PATH, "w") as f:
        json.dump(sorted(all_ips), f, indent=2)


def main():
    existing = load_existing()
    fetched = fetch()
    new_ips = fetched - existing

    if not new_ips:
        print("[*] Aucune nouvelle IP detectee.")
        print(f"[*] Total IPs restantes : {len(existing)}")
        return

    all_ips = existing.union(new_ips)
    save_new(new_ips, all_ips)

    print(f"[+] {len(new_ips)} nouvelles IP ajoutees.")
    print(f"[+] Total IPs stockees : {len(all_ips)}")


if __name__ == "__main__":
    main()
