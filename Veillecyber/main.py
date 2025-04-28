import os
import time
import logging
import random
import re
from scraper import get_articles_from_site
from summarizer import summarize_text
from notifier import send_to_discord

# Sources configurables
SITES_SOURCES = [
    {"site": "https://www.lemondeinformatique.fr/actualites/lire-cybersecurite-c47/", "nom": "lemondeinformatique"},
    {"site": "https://www.bleepingcomputer.com/news/security/", "nom": "bleepingcomputer"},
    {"site": "https://www.theregister.com/security/", "nom": "theregister"},
    {"site": "https://cybernews.com", "nom": "cybernews"},
    {"site": "https://thehackernews.com", "nom": "thehackernews"},
    {"site": "https://krebsonsecurity.com", "nom": "krebsonsecurity"},
    {"site": "https://www.darkreading.com", "nom": "darkreading"},
    {"site": "https://www.zataz.com", "nom": "zataz"},
    {"site": "https://www.undernews.fr", "nom": "undernews"},
    {"site": "https://www.silicon.fr", "nom": "silicon"},
    {"site": "https://www.zdnet.fr/actualites/securite/", "nom": "zdnet"},
    {"site": "https://www.numerama.com/tag/cybersecurite", "nom": "numerama"},
    {"site": "https://www.usine-digitale.fr/", "nom": "usine_digitale"}
]

PROCESSED_FILE = "processed_articles.txt"
MAX_ARTICLES_PER_RUN = 3

# Mots-clés génériques et critiques
KEYWORDS = [
    "cyber", "sécurité", "faille", "vulnérabilité", "attaque",
    "hacker", "ransomware", "malware", "intrusion", "phishing",
    "IA", "intelligence artificielle", "LLM", "machine learning",
    "OT", "IT", "IoT", "SOC", "SIEM", "botnet", "DDoS"
]
SUPER_KEYWORDS = [
    "CVE", "zero day", "cyberattaque", "exploit", "RCE",
    "vol de données", "data leak", "breach", "APT", "Zero Trust",
    "sandboxing", "threat intelligence"
]

# Configuration du logging
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


def score_article(text):
    """Calcule un score selon la présence de mots-clés et super-mots-clés."""
    text_lower = text.lower()
    score = 0
    for kw in KEYWORDS:
        if kw.lower() in text_lower:
            score += 1
    for sk in SUPER_KEYWORDS:
        if sk.lower() in text_lower:
            score += 3
    return score


def normalize_title(title):
    return re.findall(r"\b\w+\b", title.lower())


def titles_are_similar(t1, t2, threshold=3):
    w1 = set(normalize_title(t1))
    w2 = set(normalize_title(t2))
    return len(w1 & w2) >= threshold


def collect_candidates(processed_articles, seen_titles):
    """Récupère, filtre et score les articles de toutes les sources."""
    candidates = []
    for site in random.sample(SITES_SOURCES, len(SITES_SOURCES)):
        site_url = site["site"]
        source_nom = site.get("nom")
        logging.info(f"Récupération des articles depuis {source_nom}")
        try:
            articles = get_articles_from_site(site_url)
        except Exception as e:
            logging.error(f"Erreur scraping {source_nom} : {e}")
            continue
        for article in articles:
            url = article.get("url")
            title = article.get("title", "").strip()
            content = article.get("content", "").strip()
            # Exclusions basiques
            if not url or url in processed_articles:
                continue
            if len(content) < 200:
                continue
            if any(titles_are_similar(title, t) for t in seen_titles):
                continue
            full_text = f"{title} {content}"
            sc = score_article(full_text)
            if sc > 0:
                candidates.append((sc, source_nom, title, url, content))
                seen_titles.add(title)
    return sorted(candidates, key=lambda x: x[0], reverse=True)


def main():
    logging.info("Démarrage du script de veille cybersécurité")
    processed_articles = load_processed_articles()
    seen_titles = set()
    logging.info(f"{len(processed_articles)} articles déjà traités.")

    candidates = collect_candidates(processed_articles, seen_titles)
    if not candidates:
        logging.info("Aucun article pertinent trouvé.")
        return

    to_send = candidates[:MAX_ARTICLES_PER_RUN]
    sent = 0
    for sc, source_nom, title, url, content in to_send:
        logging.info(f"Envoi article (score {sc}) : {title}")
        try:
            summary = summarize_text(content)
            if summary and send_to_discord(source_nom, title, url, summary):
                save_processed_article(url)
                sent += 1
            else:
                logging.warning(f"Échec d'envoi ou résumé vide pour {url}")
        except Exception as e:
            logging.error(f"Erreur traitement {url} : {e}")
        time.sleep(1)

    logging.info(f"{sent}/{MAX_ARTICLES_PER_RUN} articles envoyés.")
    logging.info("Traitement terminé.")


if __name__ == '__main__':
    main()