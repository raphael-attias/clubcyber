import os
import requests

# Configuration via GitHub Secrets
BLOCKLIST_URL = os.getenv("BLOCKLIST_URL")
WEBHOOK_URL_IP = os.getenv("WEBHOOK_URL_IP")

# Directories and files
BASE_DIR = os.path.dirname(__file__)
LOG_DIR = os.path.join(BASE_DIR, "logs")
SEEN_IPS_FILE = os.path.join(LOG_DIR, "seen_ips.log")


def ensure_log():
    """
    Création du dossier et du fichier de log s'ils n'existent pas.
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    if not os.path.exists(SEEN_IPS_FILE):
        open(SEEN_IPS_FILE, 'w').close()


def load_seen_ips():
    """
    Lecture des IP déjà signalées.
    """
    with open(SEEN_IPS_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())


def save_new_ips(new_ips):
    """
    Ajout des IP envoyées à la fin du fichier.
    """
    with open(SEEN_IPS_FILE, 'a') as f:
        for ip in sorted(new_ips):
            f.write(ip + '\n')


def fetch_blocklist():
    """
    Récupération et nettoyage de la blocklist distante.
    """
    response = requests.get(BLOCKLIST_URL, timeout=30)
    response.raise_for_status()
    return set(
        line.strip()
        for line in response.text.splitlines()
        if line.strip() and not line.startswith("#")
    )


def wrap_ip(ip: str) -> str:
    """
    Encapsule chaque octet de l'IP dans des crochets.
    Ex: "192.168.0.1" -> "[192].[168].[0].[1]"
    """
    return '.'.join(f'[{octet}]' for octet in ip.split('.'))


def send_discord(new_ips):
    """
    Envoi des IP en une ou plusieurs parties pour ne pas dépasser 2000 caractères,
    avec chaque octet encapsulé.
    """
    header = "**🛡️ Nouvelles IP malveillantes :**\n"
    # on wrappe chaque IP
    lines = [header] + [wrap_ip(ip) + "\n" for ip in sorted(new_ips)]
    message = "".join(lines)

    # Découpage si >2000 caractères
    parts = []
    while len(message) > 2000:
        cut = message.rfind('\n', 0, 2000)
        parts.append(message[:cut])
        message = message[cut+1:]
    parts.append(message)

    for part in parts:
        resp = requests.post(WEBHOOK_URL_IP, json={'content': part}, timeout=15)
        resp.raise_for_status()


def main():
    if not BLOCKLIST_URL:
        print("[!] BLOCKLIST_URL non défini — rien à faire.")
        return

    ensure_log()
    seen = load_seen_ips()
    current = fetch_blocklist()

    new_ips = current - seen
    if not new_ips:
        print("[*] Aucune nouvelle IP.")
        return

    if WEBHOOK_URL_IP:
        send_discord(new_ips)
    else:
        print("[!] WEBHOOK_URL_IP non défini — notification Discord ignorée.")

    # On enregistre les IP vues même sans webhook, pour éviter de tout renvoyer
    # au prochain passage une fois le webhook configuré.
    save_new_ips(new_ips)
    print(f"[+] {len(new_ips)} nouvelles IP traitées.")


if __name__ == '__main__':
    main()
