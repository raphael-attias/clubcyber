from newspaper import build, Article
import feedparser
import requests
import config
import logging

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def get_articles_from_site(site_url):
    articles_info = []

    # 1. Essai avec newspaper
    try:
        paper = build(
            site_url,
            language='fr',
            memoize_articles=False,
            browser_user_agent=HEADERS["User-Agent"]
        )
        for article in paper.articles[:20]:
            try:
                article.download()
                article.parse()
                if article.text and len(article.text) > 200:
                    articles_info.append({
                        "url": article.url,
                        "title": article.title,
                        "content": article.text
                    })
            except Exception as e:
                logging.warning(f"Erreur newspaper article : {e}")
    except Exception as e:
        logging.error(f"Erreur build newspaper : {e}")

    # 2. Fallback RSS si newspaper echoue ou retourne rien
    if not articles_info:
        rss_candidates = [
            f"{site_url.rstrip('/')}/rss",
            f"{site_url.rstrip('/')}/feed",
            f"{site_url.rstrip('/')}/feeds",
            f"{site_url.rstrip('/')}/atom.xml",
        ]
        # Flux RSS specifiques par domaine
        if "theregister.com" in site_url:
            rss_candidates.append("https://www.theregister.com/security/headlines.atom")
        if "bleepingcomputer.com" in site_url:
            rss_candidates.append("https://www.bleepingcomputer.com/feed/")
        if "cert.ssi.gouv.fr" in site_url:
            rss_candidates.append("https://www.cert.ssi.gouv.fr/feed/")

        for rss_url in rss_candidates:
            if not rss_url:
                continue
            try:
                feed = feedparser.parse(rss_url, request_headers=HEADERS)
                if feed.bozo == 0 and feed.entries:
                    for entry in feed.entries[:10]:
                        url = entry.get("link")
                        title = entry.get("title", "")
                        content = (
                            entry.get("summary", "")
                            or (entry.get("content") and entry["content"][0].get("value", ""))
                        )
                        if url and content and len(content) > 200:
                            articles_info.append({
                                "url": url,
                                "title": title,
                                "content": content
                            })
                    logging.info(f"[+] Articles RSS recuperes via {rss_url} ({len(articles_info)})")
                    break
            except Exception as e:
                logging.warning(f"Erreur RSS {rss_url} : {e}")

    return articles_info
