import requests
import os
from datetime import datetime

# Configuration via GitHub Secrets
BLOCKLIST_URL = os.getenv("BLOCKLIST_URL")
WEBHOOK_URL_IP = os.getenv("WEBHOOK_URL_IP")

LOG_DIR = "clubcyber/barracuda/logs"
SEEN_IPS_FILE = os.path.join(LOG_DIR, "seen_ips.log")
MESSAGE_LOG_FILE = os.path.join(LOG_DIR, "messages_sent.log")

def load_seen_ips():
    if not os.path.exists(SEEN_IPS_FILE):
        return set()
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
    response = requests.get(BLOCKLIST_URL)
    response.raise_for_status()
    return [line.strip() for line in response.text.splitlines() if line.strip()]

def send_discord_message(new_ips):
    if not new_ips:
        return

    message = "**🛡️ Nouvelles IP malveillantes détectées :**\n" + "\n".join(new_ips)

    if len(message) > 2000:
        message = message[:1997] + "..."

    payload = {"content": message}
    response = requests.post(WEBHOOK_URL_IP, json=payload)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        log_message(f"[ERREUR Discord] Statut: {response.status_code}, Réponse: {response.text}")
        raise
    log_message(message)


def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    seen_ips = load_seen_ips()
    current_ips = set(fetch_blocklist())
    new_ips = current_ips - seen_ips

    if new_ips:
        send_discord_message(sorted(new_ips))
        save_seen_ips(new_ips)
    else:
        log_message("Aucune nouvelle IP détectée.")

if __name__ == "__main__":
    main()
