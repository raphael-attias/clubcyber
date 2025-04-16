import requests
import json
from config import DISCORD_WEBHOOK_URL

def send_to_discord(source_nom, article_title, article_url, summary):
    data = {
        "content": f"**Source : {source_nom}**\n**Titre : {article_title}**\n**Lien :** {article_url}\n\n**Résumé :**\n{summary}"
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(data), headers=headers)
        if response.status_code in [200, 204]:
            print(f"Message envoyé avec succès pour {article_title}")
        else:
            print(f"Erreur lors de l'envoi sur Discord: {response.status_code}")
    except Exception as e:
        print(f"Erreur de connexion à Discord: {e}")