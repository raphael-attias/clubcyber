import os
import time
import logging
import threading
import random
import re
import requests
from scraper import get_articles_from_site
from summarizer import summarize_text
from notifier import send_to_discord

SITES_SOURCES = [
    {"site": "https://www.lemondeinformatique.fr/actualites/lire-cybersecurite-c47/", "nom": "lemondeinfor"},
    {"site": "https://www.bleepingcomputer.com/news/security/", "nom": "bleepingcomputer"},
    {"site": "https://www.theregister.com/security/", "nom": "theregister"}
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
        logging.FileHandler("App.log", mode="a"),
        logging.StreamHandler()
    ]
)

def load_processed_articles():
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_processed_article(url):
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(url + "\n")

def is_relevant_article(article):
    title = article.get("title", "").lower()
    content = article.get("content", "").lower()
    text = f"{title} {content}"
    return any(k.lower() in text for k in KEYWORDS) and len(content) > 200

def is_critical_article(article):
    title = article.get("title", "").lower()
    content = article.get("content", "").lower()
    text = f"{title} {content}"
    return any(k.lower() in text for k in SUPER_KEYWORDS)

def normalize_title(title):
    return re.findall(r"\b\w+\b", title.lower())

def titles_are_similar(title1, title2, threshold=3):
    words1 = set(normalize_title(title1))
    words2 = set(normalize_title(title2))
    return len(words1 & words2) >= threshold

def process_site_pass(site, processed_articles, seen_titles, strict=True):
    global articles_sent
    site_url = site["site"]
    source_nom = site.get("nom", site_url)
    logging.info(f"Traitement de la source : {source_nom}")
    articles = get_articles_from_site(site_url)
    for article in articles:
        with lock:
            if articles_sent >= MAX_ARTICLES_PER_RUN:
                return
        url = article.get("url")
        title = article.get("title", "Sans titre")
        content = article.get("content", "")
        if not url or len(content) < 200:
            continue
        if url in processed_articles:
            continue
        if strict and not is_relevant_article(article):
            continue
        with lock:
            if any(titles_are_similar(title, t) for t in seen_titles):
                continue
            seen_titles.add(title)

        logging.info(f"Envoi de l'article {'CRITIQUE' if is_critical_article(article) else 'pertinent' if strict else 'fallback'}: {title}")
        try:
            summary = summarize_text(content)
            if summary:
                if send_to_discord(source_nom, title, url, summary):
                    processed_articles.add(url)
                    save_processed_article(url)
                    with lock:
                        articles_sent += 1
                        logging.info(f"Article envoyé [{articles_sent}/{MAX_ARTICLES_PER_RUN}]")
                else:
                    logging.warning(f"Échec de l'envoi sur Discord pour {url}")
            else:
                logging.warning(f"Aucun résumé généré pour {url}")
        except Exception as e:
            logging.error(f"Erreur traitement {url}: {e}")
        time.sleep(2)
        with lock:
            if articles_sent >= MAX_ARTICLES_PER_RUN:
                return

def main():
    global articles_sent
    logging.info("Démarrage du script de veille cybersécurité")
    processed_articles = load_processed_articles()
    seen_titles = set()
    logging.info(f"{len(processed_articles)} articles déjà traités.")
    random.shuffle(SITES_SOURCES)
    for site in SITES_SOURCES:
        process_site_pass(site, processed_articles, seen_titles, strict=True)
        if articles_sent >= MAX_ARTICLES_PER_RUN:
            break
    if articles_sent < MAX_ARTICLES_PER_RUN:
        logging.info(f"Seulement {articles_sent} articles envoyés, passe fallback pour compléter")
        for site in SITES_SOURCES:
            process_site_pass(site, processed_articles, seen_titles, strict=False)
            if articles_sent >= MAX_ARTICLES_PER_RUN:
                break
    logging.info("Traitement terminé.")

if __name__ == '__main__':
    main()
