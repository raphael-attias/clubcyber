#!/usr/bin/env python3
"""
geolocate.py
Combine geoloc via IPInfo + fallback IA (Mistral) si coords manquantes.
Traite les IP une par une, passe a la suivante meme si l'IA echoue,
et evite les IP deja traitees.
"""

import os
import time
import json
import re
import requests
import pandas as pd
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from mistralai import Mistral

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# --- Config ---
IPINFO_API_URL      = "https://ipinfo.io/"
IPINFO_TOKEN        = os.getenv("IPINFO_TOKEN", "")
MISTRAL_API_KEY     = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL       = os.getenv("MISTRAL_MODEL", "mistral-large-latest")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

DATA_DIR   = os.path.join(os.path.dirname(__file__), "..", "data")
INPUT_CSV  = os.path.join(DATA_DIR, "ips.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "geo_enriched.csv")

SYSTEM_PROMPT = (
    "Tu es un service de geolocalisation d'adresses IP.\n"
    "Quand je te fournis une adresse IP, tu dois d'abord tenter d'obtenir ses coordonnees GPS exactes (latitude, longitude).\n"
    "Si les coordonnees GPS exactes ne sont pas disponibles, tu recuperes alors les coordonnees (latitude, longitude) du centre de la ville d'origine de cette IP.\n"
    "Tu repondras uniquement par un objet JSON formate exactement comme :\n"
    "{\n"
    "  \"ip\": \"1.2.3.4\",\n"
    "  \"source\": \"gps\" | \"city\",\n"
    "  \"latitude\": 0.0,\n"
    "  \"longitude\": 0.0,\n"
    "  \"city\": \"\",\n"
    "  \"region\": \"\",\n"
    "  \"country\": \"\"\n"
    "}\n"
    "sans texte additionnel."
)

# Session HTTP avec retry
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount("https://", HTTPAdapter(max_retries=retries))


def ensure_output_csv():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(OUTPUT_CSV) or os.path.getsize(OUTPUT_CSV) == 0:
        df = pd.DataFrame(columns=["ip", "source", "latitude", "longitude", "city", "region", "country"])
        df.to_csv(OUTPUT_CSV, index=False)


def load_done_ips():
    df = pd.read_csv(OUTPUT_CSV)
    return set(df["ip"].astype(str).tolist())


def call_ipinfo(ip):
    if not IPINFO_TOKEN:
        raise RuntimeError("IPINFO_TOKEN manquant")
    url = f"{IPINFO_API_URL}{ip}/json"
    resp = session.get(url, params={"token": IPINFO_TOKEN}, timeout=10)
    resp.raise_for_status()
    d = resp.json()
    lat, lon = None, None
    if "loc" in d and d["loc"]:
        parts = d["loc"].split(",")
        if len(parts) == 2:
            lat, lon = float(parts[0]), float(parts[1])
    return {
        "ip": ip,
        "source": "ipinfo",
        "latitude": lat,
        "longitude": lon,
        "city": d.get("city"),
        "region": d.get("region"),
        "country": d.get("country"),
    }


def call_mistral(ip, client):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": ip},
    ]
    resp = client.chat.complete(model=MISTRAL_MODEL, messages=messages)
    text = resp.choices[0].message.content.strip()
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}$", text, re.DOTALL)
    json_str = match.group(0) if match else text
    return json.loads(json_str)


def enrich_ip(ip, mistral_client):
    # Tentative IPInfo
    try:
        rec = call_ipinfo(ip)
        if rec["latitude"] is not None and rec["longitude"] is not None:
            return rec
        raise ValueError("coords manquantes IPInfo")
    except Exception as e:
        print(f"[*] IPInfo echouee ({e}), fallback Mistral pour {ip}")

    # Fallback Mistral
    if not mistral_client:
        print(f"[!] Pas de client Mistral disponible, IP {ip} ignoree.")
        return None
    try:
        rec = call_mistral(ip, mistral_client)
        if rec.get("latitude") is None or rec.get("longitude") is None:
            raise ValueError("coords manquantes Mistral")
        rec["source"] = rec.get("source", "ai")
        return rec
    except Exception as e:
        print(f"[!] Mistral fallback echoue pour {ip}: {e}")
        return None


def notify_discord(message):
    if not DISCORD_WEBHOOK_URL:
        print("[!] DISCORD_WEBHOOK_URL non defini, pas de notification.")
        return
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=5)
        resp.raise_for_status()
        print("[+] Notification Discord envoyee.")
    except Exception as e:
        print(f"[!] Echec notification Discord: {e}")


def main():
    # Validation des secrets DANS main() — jamais au niveau module
    if not IPINFO_TOKEN:
        print("[!] IPINFO_TOKEN manquant — geolocalisation IPInfo desactivee, fallback Mistral uniquement.")

    mistral_client = None
    if MISTRAL_API_KEY:
        mistral_client = Mistral(api_key=MISTRAL_API_KEY)
    else:
        print("[!] MISTRAL_API_KEY manquant — fallback Mistral desactive.")

    ensure_output_csv()
    done = load_done_ips()

    if not os.path.exists(INPUT_CSV):
        print(f"[!] Fichier source introuvable : {INPUT_CSV}")
        return

    ips = pd.read_csv(INPUT_CSV, header=None)[0].astype(str).tolist()
    to_do = [ip for ip in ips if ip not in done]

    if not to_do:
        print("[+] Aucune nouvelle IP a enrichir.")
        return

    print(f"[*] {len(to_do)} IPs a traiter...")
    success = 0
    for idx, ip in enumerate(to_do, start=1):
        print(f"[*] ({idx}/{len(to_do)}) {ip}")
        rec = enrich_ip(ip, mistral_client)
        if rec is None:
            print(f"[!] Echec total pour {ip}, on passe.")
            continue
        pd.DataFrame([rec]).to_csv(OUTPUT_CSV, mode="a", index=False, header=False)
        success += 1
        time.sleep(0.5)

    print(f"[+] Termine : {success}/{len(to_do)} IPs enrichies.")
    notify_discord(f":white_check_mark: Geolocate termine : {success}/{len(to_do)} IPs enrichies.")


if __name__ == "__main__":
    main()
