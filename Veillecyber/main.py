import os
import time
import logging
import threading
import random
from scraper import get_articles_from_site
from summarizer import summarize_text
from notifier import send_to_discord

# Vos sources
SITES_SOURCES = [
    #{"site": "https://korben.info/", "nom": "korben"},
    #{"site": "https://www.lemondeinformatique.fr/", "nom": "lemondeinfor"},
    {"site": "https://www.bleepingcomputer.com/", "nom": "bleepingcomputer"},
    {"site": "https://www.theregister.com/security/", "nom": "theregister"},
    {"site": "https://www.darkreading.com/", "nom": "darkreading.com"}
]

# Fichier pour suivre les articles déjà envoyés
PROCESSED_FILE = "processed_articles.txt"

# Limite d'envoi par exécution
MAX_ARTICLES_PER_RUN = 3

# Mots-clés classiques
KEYWORDS = [
    "cyber", "sécurité", "faille", "vulnérabilité", "attaque",
    "hacker", "ransomware", "malware", "intrusion", "phishing",
    "IA", "intelligence artificielle", "LLM", "machine learning",
    "OT", "IT"
]

# Super mots-clés pour les articles critiques
SUPER_KEYWORDS = [
    "CVE", "zero day", "cyberattaque", "exploit", "RCE", "vol de données", "data leak", "breach"
]

# Compteur global et verrou
articles_sent = 0
lock = threading.Lock()

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

def load_processed_articles():
    """Charge les articles déjà traités depuis le fichier."""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_processed_article(url):
    """Enregistre un article dans le fichier des articles traités."""
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def is_relevant_article(article):
    """Vérifie si l'article est pertinent (mots-clés et contenu suffisant)."""
    title = article.get("title", "").lower()
    content = article.get("content", "").lower()
    text = f"{title} {content}"
    return (
        any(k.lower() in text for k in KEYWORDS) and len(content) > 200
    )

def is_critical_article(article):
    """Vérifie si l'article contient des super mots-clés."""
    title = article.get("title", "").lower()
    content = article.get("content", "").lower()
    text = f"{title} {content}"
    return any(k.lower() in text for k in SUPER_KEYWORDS)

def process_site_thread(site, processed_articles):
    global articles_sent
    site_url = site["site"]
    source_nom = site.get("nom", site_url)
    logging.info(f"Traitement de la source : {source_nom} - {site_url}")

    articles = get_articles_from_site(site_url)
    for article in articles:
        url = article.get("url")
        if not url:
            continue

        with lock:
            if articles_sent >= MAX_ARTICLES_PER_RUN:
                logging.info("Limite d'articles atteinte, arrêt du thread.")
                return

        if url in processed_articles:
            logging.info(f"Article déjà traité : {url}")
            continue

        if not is_relevant_article(article):
            logging.info(f"Article non pertinent : {article.get('title', 'Sans titre')}")
            continue

        is_critical = is_critical_article(article)
        logging.info(f"Article pertinent{' (CRITIQUE)' if is_critical else ''} : {article.get('title', 'Sans titre')}")

        try:
            summary = summarize_text(article["content"])
            if summary:
                send_to_discord(source_nom, article["title"], url, summary)
                processed_articles.add(url)
                save_processed_article(url)
                with lock:
                    articles_sent += 1
                    logging.info(f"Article envoyé [{articles_sent}/{MAX_ARTICLES_PER_RUN}]")
            else:
                logging.warning(f"Résumé vide pour l'article : {url}")
        except Exception as e:
            logging.error(f"Erreur lors du traitement de l'article {url}: {e}")

        if articles_sent >= MAX_ARTICLES_PER_RUN:
            return

        time.sleep(2)

def main():
    processed_articles = load_processed_articles()
    logging.info(f"{len(processed_articles)} articles déjà traités.")

    random.shuffle(SITES_SOURCES)
    threads = []

    for site in SITES_SOURCES:
        thread = threading.Thread(target=process_site_thread, args=(site, processed_articles))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    logging.info("Traitement terminé.")

if __name__ == '__main__':
    main()