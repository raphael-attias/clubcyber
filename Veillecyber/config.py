import os

# Les variables d'environnement sont directement accessibles sans besoin de charger un fichier .env
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
MISTRAL_API_ENDPOINT = os.getenv("MISTRAL_API_ENDPOINT")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
