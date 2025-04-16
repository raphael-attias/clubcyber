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
    {"site": "https://www.lemondeinformatique.fr/", "nom": "lemondeinfor"},
    {"site": "https://www.bleepingcomputer.com/", "nom": "bleepingcomputer"},
    {"site": "https://www.theregister.com/security/", "nom": "theregister"},
    {"site": "https://www.darkreading.com/", "nom": "darkreading.com"}
]

# Fichier pour suivre les articles déjà traités
PROCESSED_FILE = "processed_articles.txt"

# Limite d'envoi par exécution (max 3 articles par run)
MAX_ARTICLES_PER_RUN = 3

# Liste de mots-clés spécifiques à la cybersécurité et à l'IA/LLM
KEYWORDS = [
    "cyber", "sécurité", "faille", "vulnérabilité", "attaque",
    "hacker", "ransomware", "malware", "intrusion", "phishing",
    "IA", "intelligence artificielle", "LLM", "machine learning",
    "OT", "IT"
]

# Variable globale et verrou pour le comptage des articles envoyés
articles_sent = 0
lock = threading.Lock()

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

def load_processed_articles():
    """Charge les URLs déjà traitées depuis le fichier."""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_processed_article(url):
    """Enregistre une URL dans le fichier des articles traités."""
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def is_relevant_article(article):
    """
    Retourne True si l'article contient au moins un des mots-clés définis
    dans son titre ou son contenu (et si le contenu est suffisamment long).
    """
    title = article.get("title", "").lower()
    content = article.get("content", "").lower()
    text_to_check = f"{title} {content}"
    return any(keyword.lower() in text_to_check for keyword in KEYWORDS) and len(content) > 200

def process_site_thread(site, processed_articles):
    """
    Fonction exécutée dans un thread pour traiter une source.
    Pour chaque article, vérifie s'il n'a pas déjà été traité,
    s'il est pertinent selon les mots-clés, et si la limite globale n'est pas atteinte.
    """
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
                logging.info("Limite d'articles global atteinte, arrêt du thread.")
                return

        if url in processed_articles:
            logging.info(f"Article déjà traité : {url}")
            continue

        if not is_relevant_article(article):
            logging.info(f"Article non pertinent : {article.get('title', 'Sans titre')}")
            continue

        # Traitement de l'article pertinent
        logging.info(f"Traitement de l'article pertinent : {article.get('title', 'Sans titre')}")
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

        with lock:
            if articles_sent >= MAX_ARTICLES_PER_RUN:
                logging.info("Limite d'articles global atteinte, arrêt du thread.")
                return

        # Pause courte pour réduire la charge sur les serveurs de source
        time.sleep(2)

def main():
    processed_articles = load_processed_articles()
    logging.info(f"{len(processed_articles)} articles déjà traités.")

    # Mélanger aléatoirement l'ordre des sources pour éviter de toujours traiter la même en premier.
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
