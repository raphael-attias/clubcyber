import os
import time
import logging
import random
import re
from unidecode import unidecode
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
    "ia", "intelligence artificielle", "llm", "machine learning",
    "ot", "it", "iot", "soc", "siem", "botnet", "ddos"
]
SUPER_KEYWORDS = [
    "cve", "zero day", "cyberattaque", "exploit", "rce",
    "vol de données", "data leak", "breach", "apt", "zero trust",
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

def clean_url(url):
    """Nettoie les paramètres et fragments d'URL."""
    if not url:
        return None
    return url.split('?')[0].split('#')[0].rstrip('/').strip()

def load_processed_articles():
    """Charge les URLs déjà traitées."""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        return {clean_url(line) for line in f if line.strip()}

def save_processed_article(url):
    """Enregistre une URL traitée."""
    with open(PROCESSED_FILE, "a", encoding="utf-8") as f:
        f.write(clean_url(url) + "\n")

def score_article(text):
    """Calcule un score selon la présence de mots-clés et super-mots-clés."""
    norm = unidecode(text.lower())
    score = sum(1 for kw in KEYWORDS if unidecode(kw) in norm)
    score += sum(3 for sk in SUPER_KEYWORDS if unidecode(sk) in norm)
    return score

def normalize_title(title):
    """Extrait les mots du titre."""
    return re.findall(r"\b\w+\b", unidecode(title.lower()))

def titles_are_similar(t1, t2, threshold=3):
    """Détecte les titres trop proches."""
    w1 = set(normalize_title(t1))
    w2 = set(normalize_title(t2))
    return len(w1 & w2) >= threshold

def collect_candidates(processed_articles, seen_titles):
    """Récupère, filtre et score les articles de toutes les sources."""
    candidates = []
    for site in random.sample(SITES_SOURCES, len(SITES_SOURCES)):
        source_nom = site["nom"]
        logging.info(f"Scraping {source_nom}")
        try:
            articles = get_articles_from_site(site["site"])
        except Exception as e:
            logging.error(f"Erreur scraping {source_nom}: {e}")
            continue
        for art in articles:
            url = clean_url(art.get("url"))
            title = art.get("title", "").strip()
            content = art.get("content", "").strip()
            if not url or url in processed_articles:
                continue
            if len(content) < 200:
                continue
            if any(titles_are_similar(title, t) for t in seen_titles):
                continue
            score = score_article(f"{title} {content}")
            if score > 0:
                candidates.append((score, source_nom, title, url, content))
                seen_titles.add(title)
    return sorted(candidates, key=lambda x: x[0], reverse=True)

def main():
    logging.info("Démarrage du script de veille cybersécurité")
    processed = load_processed_articles()
    seen = set()
    logging.info(f"{len(processed)} articles déjà traités.")
    candidates = collect_candidates(processed, seen)
    if not candidates:
        logging.info("Aucun article pertinent trouvé.")
        return

    to_send = candidates[:MAX_ARTICLES_PER_RUN]
    sent = 0
    for score, src, title, url, content in to_send:
        logging.info(f"Envoi (score {score}) : {title}")
        try:
            summary = summarize_text(content)
            if summary and send_to_discord(src, title, url, summary):
                save_processed_article(url)
                sent += 1
            else:
                logging.warning(f"Échec envoi ou résumé vide : {url}")
        except Exception as e:
            logging.error(f"Erreur sur {url}: {e}")
        time.sleep(1)

    logging.info(f"{sent}/{MAX_ARTICLES_PER_RUN} articles envoyés.")
    logging.info("Traitement terminé.")

if __name__ == "__main__":
    main()

