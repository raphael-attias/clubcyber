from newspaper import build, Article
import feedparser
import requests
import logging


def get_articles_from_site(site_url):
    articles_info = []

    # 1. Essai avec newspaper
    try:
        paper = build(site_url, language='fr', memoize_articles=False)
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
                logging.warning(f"Erreur newspaper : {e}")
    except Exception as e:
        logging.error(f"Erreur build newspaper : {e}")

    if not articles_info:
        rss_candidates = [
            f"{site_url.rstrip('/')}/rss",
            f"{site_url.rstrip('/')}/feed",
            f"{site_url.rstrip('/')}/feeds",
            f"{site_url.rstrip('/')}/atom.xml",
            "https://www.theregister.com/security/headlines.atom" if "theregister.com" in site_url else None
        ]
        for rss_url in rss_candidates:
            if not rss_url:
                continue
            try:
                feed = feedparser.parse(rss_url)
                if feed.bozo == 0 and feed.entries:
                    for entry in feed.entries[:10]:
                        url = entry.get("link")
                        title = entry.get("title", "")
                        content = entry.get("summary", "") or \
                                  (entry.get("content") and entry["content"][0].get("value", ""))
                        if url and content and len(content) > 200:
                            articles_info.append({
                                "url": url,
                                "title": title,
                                "content": content
                            })
                    logging.info(f"Articles RSS récupérés via {rss_url}")
                    break
            except Exception as e:
                logging.warning(f"Erreur RSS {rss_url} : {e}")

    return articles_info