import os
import time
import logging
import threading
import random
import re  # Ajout de l'import manquant
import requests
from scraper import get_articles_from_site
from summarizer import summarize_text
from notifier import send_to_discord

# Vos sources mises à jour avec des URLs plus précises
SITES_SOURCES = [
    {"site": "https://korben.info/category/securite", "nom": "korben"},
    {"site": "https://www.lemondeinformatique.fr/actualites/lire-cybersecurite-c47/", "nom": "lemondeinfor"},
    {"site": "https://www.bleepingcomputer.com/news/security/", "nom": "bleepingcomputer"},
    {"site": "https://www.theregister.com/security/", "nom": "theregister"},
    # Dark Reading a besoin d'un traitement spécial car il bloque les robots
    # {"site": "https://www.darkreading.com/", "nom": "darkreading.com"}
]

PROCESSED_FILE = "processed_articles.txt"
MAX_ARTICLES_PER_RUN = 3

KEYWORDS = [
    "cyber", "sécurité", "faille", "vulnérabilité", "attaque",
    "hacker", "ransomware", "malware", "intrusion", "phishing",
    "IA", "intelligence artificielle", "LLM", "machine learning",
    "OT", "IT"
]

SUPER_KEYWORDS = [
    "CVE", "zero day", "cyberattaque", "exploit", "RCE", "vol de données", "data leak", "breach"
]

articles_sent = 0
lock = threading.Lock()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("App.log", mode="a"),  # Mode append pour éviter d'écraser
        logging.StreamHandler()
    ]
)

def load_processed_articles():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    try:
        with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        logging.error(f"Erreur lors de la lecture de {PROCESSED_FILE}: {e}")
        return set()

def save_processed_article(url):
    try:
        with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
            f.write(url + "\n")
        return True
    except Exception as e:
        logging.error(f"Erreur lors de l'écriture dans {PROCESSED_FILE}: {e}")
        return False

def is_relevant_article(article):
    title = article.get("title", "").lower()
    content = article.get("content", "").lower()
    text = f"{title} {content}"
    return (
        any(k.lower() in text for k in KEYWORDS) and len(content) > 200
    )

def is_critical_article(article):
    title = article.get("title", "").lower()
    content = article.get("content", "").lower()
    text = f"{title} {content}"
    return any(k.lower() in text for k in SUPER_KEYWORDS)

def normalize_title(title):
    # Utiliser re.findall pour extraire les mots
    return re.findall(r"\b\w+\b", title.lower())

def titles_are_similar(title1, title2, threshold=3):
    words1 = set(normalize_title(title1))
    words2 = set(normalize_title(title2))
    return len(words1 & words2) >= threshold

def check_site_availability(url):
    """Vérifier si un site est accessible avant de le scraper"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"Site {url} inaccessible: {e}")
        return False

def process_site_thread(site, processed_articles, seen_titles):
    global articles_sent
    site_url = site["site"]
    source_nom = site.get("nom", site_url)
    
    logging.info(f"Traitement de la source : {source_nom} - {site_url}")
    
    # Vérifier si le site est accessible avant de continuer
    if not check_site_availability(site_url):
        logging.error(f"Site {site_url} inaccessible, abandon du traitement pour cette source")
        return

    try:
        articles = get_articles_from_site(site_url)
        
        if not articles:
            logging.warning(f"Aucun article trouvé pour {source_nom} - {site_url}")
            return
        
        for article in articles:
            url = article.get("url")
            title = article.get("title", "Sans titre")
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
                logging.debug(f"Article non pertinent : {title}")
                continue

            with lock:
                if any(titles_are_similar(title, seen_title) for seen_title in seen_titles):
                    logging.info(f"Titre similaire déjà traité : {title}")
                    continue
                seen_titles.add(title)

            is_critical = is_critical_article(article)
            logging.info(f"Traitement de l'article pertinent{' (CRITIQUE)' if is_critical else ''} : {title}")

            try:
                summary = summarize_text(article["content"])
                if summary:
                    success = send_to_discord(source_nom, title, url, summary)
                    if success:
                        processed_articles.add(url)
                        save_processed_article(url)
                        with lock:
                            articles_sent += 1
                            logging.info(f"Article envoyé [{articles_sent}/{MAX_ARTICLES_PER_RUN}]")
                    else:
                        logging.error(f"Échec de l'envoi sur Discord pour l'article : {url}")
                else:
                    logging.warning(f"Résumé vide pour l'article : {url}")
            except Exception as e:
                logging.error(f"Erreur lors du traitement de l'article {url}: {e}")

            with lock:
                if articles_sent >= MAX_ARTICLES_PER_RUN:
                    logging.info("Limite d'articles global atteinte, arrêt du thread.")
                    return

            # Pause pour éviter de surcharger l'API ou le site
            time.sleep(2)
    except Exception as e:
        logging.error(f"Erreur globale lors du traitement de {source_nom}: {e}")

def main():
    global articles_sent
    
    # Logging du début de l'exécution
    logging.info("Démarrage du script de veille cybersécurité")

    # Chargement des articles déjà traités
    processed_articles = load_processed_articles()
    seen_titles = set()
    logging.info(f"{len(processed_articles)} articles déjà traités.")

    # Mélange des sources pour varier l'ordre de traitement
    random.shuffle(SITES_SOURCES)
    threads = []

    # Création et démarrage des threads pour chaque source
    for site in SITES_SOURCES:
        thread = threading.Thread(target=process_site_thread, args=(site, processed_articles, seen_titles))
        threads.append(thread)
        thread.start()
        # Légère pause entre chaque démarrage de thread
        time.sleep(1)

    # Attente de la fin de tous les threads
    for thread in threads:
        thread.join()

    logging.info("Traitement terminé.")

if __name__ == '__main__':
    main()