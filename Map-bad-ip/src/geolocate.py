#!/usr/bin/env python3
"""
geolocate.py
Pour chaque IP dans data/ips.csv, interroge l’API IPAPI.CO pour récupérer
latitude, longitude, pays, organisation/ASN, puis enrichit data/geo_enriched.csv
en évitant les doublons.
"""

import os
import time
import csv
import requests
import pandas as pd
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

API_URL = "https://ipapi.co/{ip}/json/"
API_TOKEN = os.getenv("IPAPI_TOKEN", "")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INPUT_CSV = os.path.join(DATA_DIR, "ips.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")

# Setup session with retry/backoff
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def load_geo_existing():
    if os.path.exists(OUTPUT_CSV):
        return pd.read_csv(OUTPUT_CSV)["ip"].astype(str).tolist()
    return []

def enrich_ip(ip):
    url = API_URL.format(ip=ip)
    headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}
    resp = session.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "ip": ip,
        "country": data.get("country_name", ""),
        "country_code": data.get("country", ""),
        "latitude": data.get("latitude", None),
        "longitude": data.get("longitude", None),
        "org": data.get("org", "").split(" ")[0]
    }

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    ips = pd.read_csv(INPUT_CSV, header=None)[0].astype(str).tolist()
    done = set(load_geo_existing())
    results = []
    for ip in ips:
        if ip in done:
            continue
        try:
            rec = enrich_ip(ip)
            results.append(rec)
            print(f"[+] Enriched {ip}")
        except Exception as e:
            print(f"[!] Error {ip}: {e}")
        time.sleep(1)  # respecter les limites de l’API
    if results:
        df = pd.DataFrame(results)
        if os.path.exists(OUTPUT_CSV):
            df.to_csv(OUTPUT_CSV, mode="a", index=False, header=False)
        else:
            df.to_csv(OUTPUT_CSV, index=False)
        print(f"[+] {len(results)} nouvelles lignes ajoutées.")
    else:
        print("[*] Rien à enrichir.")

if __name__ == "__main__":
    main()
