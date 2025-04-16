from newspaper import build

def get_articles_from_site(site_url):
    try:
        paper = build(site_url, language='fr', memoize_articles=False)
        articles_info = []
        for article in paper.articles:
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
                print(f"Erreur lors du traitement de l'article {article.url} : {e}")
        return articles_info
    except Exception as e:
        print(f"Erreur lors de la construction pour {site_url} : {e}")
        return []