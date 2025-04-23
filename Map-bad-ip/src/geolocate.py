#!/usr/bin/env python3
"""
geolocate.py
Pour chaque IP dans data/ips.csv, interroge l’API pour récupérer
latitude, longitude, pays, organisation/ASN, puis enrichit data/geo_enriched.csv
en évitant les doublons. Traite les IPs par tranches de 5.
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

API_URL = "https://ipgeolocation.abstractapi.com/v1/?api_key={API_KEY}&ip_address={ip}"
API_KEY = os.getenv("ABSTRACT_API_KEY", "")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
INPUT_CSV = os.path.join(DATA_DIR, "ips.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")

# Setup session with retry/backoff
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))

def check_or_create_csv():
    """Vérifie si le fichier CSV existe, sinon le crée avec un en-tête."""
    if not os.path.exists(OUTPUT_CSV):
        # Si le fichier n'existe pas, on le crée avec l'en-tête
        df = pd.DataFrame(columns=["ip", "country", "country_code", "latitude", "longitude", "org"])
        df.to_csv(OUTPUT_CSV, mode="w", index=False)

check_or_create_csv()

def load_geo_existing():
    """Charge les IPs déjà enrichies dans geo_enriched.csv."""
    if os.path.exists(OUTPUT_CSV) and os.path.getsize(OUTPUT_CSV) > 0:
        return pd.read_csv(OUTPUT_CSV)["ip"].astype(str).tolist()
    return []

def enrich_ip(ip):
    """Enrichit une IP en récupérant les données depuis l'API."""
    url = API_URL.format(API_KEY=API_KEY, ip=ip)
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    # Log de la réponse de l'API
    print(f"Réponse de l'API pour {ip}: {response.json()}")
    
    data = response.json()
    return {
        "ip": ip,
        "country": data.get("country_name", ""),
        "country_code": data.get("country_code", ""),
        "latitude": data.get("latitude", None),
        "longitude": data.get("longitude", None),
        "org": data.get("organisation", "")
    }

def process_ips_in_batches(ips, batch_size=5):
    """Traite les IPs par lots de 5 et enrichit les données."""
    results = []
    for i in range(0, len(ips), batch_size):
        batch_ips = ips[i:i + batch_size]
        for ip in batch_ips:
            print(f"[*] Requête pour {ip}...")
            try:
                rec = enrich_ip(ip)
                results.append(rec)
                print(f"[+] Enriched {ip}")
            except Exception as e:
                print(f"[!] Erreur avec {ip} : {e}")
        if results:
            df = pd.DataFrame(results)
            df.to_csv(OUTPUT_CSV, mode="a", index=False, header=not os.path.exists(OUTPUT_CSV))
            print(f"[+] {len(results)} nouvelles lignes ajoutées.")
        time.sleep(1)  # respect des limites de l'API
    return results

def main():
    """Exécute le processus d'enrichissement des IPs."""
    os.makedirs(DATA_DIR, exist_ok=True)
    ips = pd.read_csv(INPUT_CSV, header=None)[0].astype(str).tolist()
    done = set(load_geo_existing())  # Charge les IPs déjà enrichies
    ips_to_process = [ip for ip in ips if ip not in done]

    if not ips_to_process:
        print("[*] Aucune IP à enrichir.")
    else:
        process_ips_in_batches(ips_to_process)

if __name__ == "__main__":
    main()
