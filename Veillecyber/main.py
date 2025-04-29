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
    {"site": "https://www.usine-digitale.fr/", "nom": "usine_digitale"},
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
    """Calcule un score basé sur le nombre de mots-clés distincts."""
    text_lower = text.lower()
    matched = set()
    score = 0
    # Comptage distinct de mots-clés
    for kw in KEYWORDS:
        if kw.lower() in text_lower:
            matched.add(kw)
    for sk in SUPER_KEYWORDS:
        if sk.lower() in text_lower:
            matched.add(sk)
            score += 2  # pondération plus lourde par super-keyword
    # Un point par mot-clé générique
    score += len(matched - set(SUPER_KEYWORDS))
    return score


def normalize_title(title):
    return re.findall(r"\b\w+\b", title.lower())


def titles_are_similar(t1, t2, threshold=3):
    w1 = set(normalize_title(t1))
    w2 = set(normalize_title(t2))
    return len(w1 & w2) >= threshold


def collect_best_articles(processed_articles, max_count=MAX_ARTICLES_PER_RUN):
    """
    Récupère et retourne les `max_count` articles les mieux notés parmi toutes les sources.
    """
    candidates = []
    seen_titles = set()
    # Récupération et scoring
    for site in SITES_SOURCES:
        source = site["nom"]
        logging.info(f"Scraping {source}")
        try:
            articles = get_articles_from_site(site["site"])
        except Exception as e:
            logging.error(f"Erreur scraping {source} : {e}")
            continue
        for art in articles:
            url = art.get("url")
            title = art.get("title", "").strip()
            content = art.get("content", "").strip()
            # Filtrages de base
            if not url or url in processed_articles:
                continue
            if len(content) < 200:
                continue
            if any(titles_are_similar(title, t) for t in seen_titles):
                continue
            score = score_article(f"{title} {content}")
            if score > 0:
                candidates.append({
                    "score": score,
                    "source": source,
                    "title": title,
                    "url": url,
                    "content": content
                })
                seen_titles.add(title)
    # Tri et sélection
    top_articles = sorted(candidates, key=lambda x: x["score"], reverse=True)[:max_count]
    return top_articles


def main():
    logging.info("Démarrage du script de veille cybersécurité")
    processed = load_processed_articles()
    logging.info(f"{len(processed)} articles déjà traités.")

    best_articles = collect_best_articles(processed)
    if not best_articles:
        logging.info("Aucun article pertinent trouvé.")
        return

    sent = 0
    for art in best_articles:
        logging.info(f"Envoi article (score {art['score']}) : {art['title']}")
        try:
            summary = summarize_text(art["content"])
            if summary and send_to_discord(art["source"], art["title"], art["url"], summary):
                save_processed_article(art["url"])
                sent += 1
            else:
                logging.warning(f"Échec envoi ou résumé vide pour {art['url']}")
        except Exception as e:
            logging.error(f"Erreur traitement {art['url']}: {e}")
        time.sleep(1)

    logging.info(f"{sent}/{len(best_articles)} articles envoyés.")
    logging.info("Traitement terminé.")

if __name__ == '__main__':
    main()