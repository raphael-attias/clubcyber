from newspaper import build, Article
import requests
import logging
from urllib.parse import urljoin

def get_articles_from_site(site_url):
    try:
        # Vérifier d'abord si le site est accessible
        try:
            response = requests.get(site_url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error(f"Impossible d'accéder à {site_url}: {e}")
            return []
            
        # Vérifier si des flux RSS sont disponibles
        rss_urls = [
            urljoin(site_url, "rss"),
            urljoin(site_url, "feed"),
            urljoin(site_url, "feeds"),
            urljoin(site_url, "atom.xml"),
            "https://www.theregister.com/security/headlines.atom" if "theregister.com" in site_url else None
        ]
        
        rss_urls = [url for url in rss_urls if url]  # Enlever les None
        
        for rss_url in rss_urls:
            try:
                response = requests.get(rss_url, timeout=5)
                if response.status_code == 200:
                    logging.info(f"Flux RSS trouvé: {rss_url}")
                    # Ici vous pourriez parser le flux RSS
                    break
            except:
                pass
        
        # Utiliser newspaper3k comme fallback
        paper = build(site_url, language='fr', memoize_articles=False)
        articles_info = []
        
        for article in paper.articles[:20]:  # Limiter le nombre d'articles à traiter
            try:
                article.download()
                article.parse()
                if article.text and len(article.text) > 200:
                    articles_info.append({
                        "url": article.url,
                        "title": article.title,
                        "content": article.text
                    })
                    logging.info(f"Article trouvé: {article.title}")
            except Exception as e:
                logging.error(f"Erreur lors du traitement de l'article {article.url} : {e}")
                
        return articles_info
    except Exception as e:
        logging.error(f"Erreur lors de la construction pour {site_url} : {e}")
        return []