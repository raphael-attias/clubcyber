#!/usr/bin/env python3
"""
geolocate_ipinfo.py
Combine géoloc via IPInfo + fallback IA (Mistral) si coords manquantes.
Traite les IP une par une, passe à la suivante même si l'IA échoue, et évite les IP déjà traitées.
Utilise l'API de ipinfo.io pour la géolocalisation principale.
À la fin : git add/commit/push et notification Discord.
"""

import os
import time
import json
import re
import requests
import pandas as pd
import subprocess
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from mistralai import Mistral

# Charger le .env situé dans src
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# --- Config IPInfo API ---
IPINFO_API_URL  = "https://ipinfo.io/"
IPINFO_TOKEN    = os.getenv("IPINFO_TOKEN", "")

# --- Config Mistral AI ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
MISTRAL_MODEL   = os.getenv("MISTRAL_MODEL", "mistral-large-latest")

# --- Config Discord webhook ---
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# --- Fichiers ---
DATA_DIR        = os.path.join(os.path.dirname(__file__), "..", "data")
INPUT_CSV       = os.path.join(DATA_DIR, "ips.csv")
OUTPUT_CSV      = os.path.join(DATA_DIR, "geo_enriched.csv")

# Prompt système pour Mistral
SYSTEM_PROMPT = (
    "Tu es un service de géolocalisation d’adresses IP.\n"
    "Quand je te fournis une adresse IP, tu dois d’abord tenter d’obtenir ses coordonnées GPS exactes (latitude, longitude).\n"
    "Si les coordonnées GPS exactes ne sont pas disponibles, tu récupères alors les coordonnées (latitude, longitude) du centre de la ville d’origine de cette IP.\n"
    "Tu répondras uniquement par un objet JSON formaté exactement comme :\n"
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
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429,500,502,503,504])
session.mount("https://", HTTPAdapter(max_retries=retries))

# Client Mistral
if not MISTRAL_API_KEY:
    raise RuntimeError("MISTRAL_API_KEY non défini dans src/.env")
mistral_client = Mistral(api_key=MISTRAL_API_KEY)


def ensure_output_csv():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(OUTPUT_CSV) or os.path.getsize(OUTPUT_CSV) == 0:
        df = pd.DataFrame(columns=["ip","source","latitude","longitude","city","region","country"])
        df.to_csv(OUTPUT_CSV, index=False)


def load_done_ips():
    df = pd.read_csv(OUTPUT_CSV)
    return set(df["ip"].astype(str).tolist())


def call_ipinfo(ip):
    if not IPINFO_TOKEN:
        raise RuntimeError("IPINFO_TOKEN non défini dans src/.env")
    url = f"{IPINFO_API_URL}{ip}/json"
    resp = session.get(url, params={"token": IPINFO_TOKEN}, timeout=10)
    resp.raise_for_status()
    d = resp.json()
    # loc au format "lat,lon"
    lat, lon = (None, None)
    if "loc" in d and d["loc"]:
        parts = d["loc"].split(',')
        if len(parts) == 2:
            lat, lon = float(parts[0]), float(parts[1])
    return {
        "ip": ip,
        "source": "ipinfo",
        "latitude": lat,
        "longitude": lon,
        "city": d.get("city"),
        "region": d.get("region"),
        "country": d.get("country")
    }


def call_mistral(ip):
    messages = [{"role":"system","content":SYSTEM_PROMPT}, {"role":"user","content":ip}]
    resp = mistral_client.chat.complete(model=MISTRAL_MODEL, messages=messages)
    text = resp.choices[0].message.content.strip()
    text = re.sub(r"^```json", "", text)
    text = re.sub(r"```$", "", text).strip()
    match = re.search(r"\{.*\}$", text, re.DOTALL)
    json_str = match.group(0) if match else text
    return json.loads(json_str)


def enrich_ip(ip):
    try:
        rec = call_ipinfo(ip)
        if rec["latitude"] is None or rec["longitude"] is None:
            raise ValueError("coords manquantes IPInfo")
        return rec
    except Exception as e:
        print(f"[*] IPInfo échouée ({e}), fallback IA pour {ip}")
    try:
        rec = call_mistral(ip)
        if rec.get("latitude") is None or rec.get("longitude") is None:
            raise ValueError("coords manquantes IA")
        rec["source"] = rec.get("source","ai")
        return rec
    except Exception as e:
        print(f"[!] IA fallback échouée pour {ip}: {e}")
        return None


def git_commit_and_push():
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", "Update geo_enriched.csv after geolocate run"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("[✔] Changes pushed to remote.")
    except subprocess.CalledProcessError as e:
        print(f"[!] Git operation failed: {e}")


def notify_discord():
    if not DISCORD_WEBHOOK_URL:
        print("[!] DISCORD_WEBHOOK_URL non défini, pas de notification Discord.")
        return
    payload = {"content": ":white_check_mark: geolocate_ipinfo.py run terminé avec succès!"}
    try:
        resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        resp.raise_for_status()
        print("[✔] Notification Discord envoyée.")
    except Exception as e:
        print(f"[!] Échec notification Discord: {e}")


def main():
    ensure_output_csv()
    done = load_done_ips()
    ips = pd.read_csv(INPUT_CSV, header=None)[0].astype(str).tolist()
    to_do = [ip for ip in ips if ip not in done]
    if not to_do:
        print("[✓] Aucune IP à enrichir.")
        return
    for idx, ip in enumerate(to_do, start=1):
        print(f"[*] ({idx}/{len(to_do)}) Enrichissement de {ip}")
        rec = enrich_ip(ip)
        if rec is None:
            print(f"[!] Échec total pour {ip}, passage à la suivante.")
            continue
        pd.DataFrame([rec]).to_csv(OUTPUT_CSV, mode="a", index=False, header=False)
        print(f"[+] {ip} traité avec source={rec['source']}")
        time.sleep(1)
    print(f"[✔] Terminé, {len(to_do)} IPs tentées.")
    git_commit_and_push()
    notify_discord()

if __name__ == "__main__":
    main()
