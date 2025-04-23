import os
import requests
from datetime import datetime

# Configuration via GitHub Secrets
BLOCKLIST_URL = os.getenv("BLOCKLIST_URL")
WEBHOOK_URL_IP = os.getenv("WEBHOOK_URL_IP")

# Dossiers
BASE_DIR = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE_DIR, "logs")
SEEN_IPS_FILE = os.path.join(LOG_DIR, "seen_ips.log")
MESSAGE_LOG_FILE = os.path.join(LOG_DIR, "messages_sent.log")

def ensure_log_files():
    """Création des fichiers de log si absents."""
    os.makedirs(LOG_DIR, exist_ok=True)
    for file_path in [SEEN_IPS_FILE, MESSAGE_LOG_FILE]:
        if not os.path.exists(file_path):
            open(file_path, "w").close()

def load_seen_ips():
    with open(SEEN_IPS_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_seen_ips(ips):
    with open(SEEN_IPS_FILE, "a") as f:
        for ip in ips:
            f.write(ip + "\n")

def log_message(text):
    with open(MESSAGE_LOG_FILE, "a") as f:
        f.write(f"[{datetime.now()}] {text}\n")

def fetch_blocklist():
    try:
        response = requests.get(BLOCKLIST_URL)
        response.raise_for_status()
        return [line.strip() for line in response.text.splitlines() if line.strip()]
    except Exception as e:
        log_message(f"[ERREUR Téléchargement] {e}")
        return []

def send_discord_message(new_ips):
    if not new_ips:
        return

    chunks = []
    chunk = "**🛡️ Nouvelles IP malveillantes détectées :**\n"
    for ip in sorted(new_ips):
        if len(chunk) + len(ip) + 1 >= 2000:
            chunks.append(chunk)
            chunk = ""
        chunk += ip + "\n"
    if chunk:
        chunks.append(chunk)

    for part in chunks:
        payload = {"content": part}
        try:
            response = requests.post(WEBHOOK_URL_IP, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            log_message(f"[ERREUR Discord] {e}")
            continue
        log_message(f"[ENVOYÉ] {len(part.splitlines())} IPs")

def main():
    ensure_log_files()
    seen_ips = load_seen_ips()
    current_ips = set(fetch_blocklist())

    new_ips = current_ips - seen_ips
    if new_ips:
        send_discord_message(new_ips)
        save_seen_ips(new_ips)
    else:
        log_message("Aucune nouvelle IP détectée.")

if __name__ == "__main__":
    main()
