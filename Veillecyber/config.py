import os
from dotenv import load_dotenv

load_dotenv()  # Charge le fichier .env

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
MISTRAL_API_ENDPOINT = os.getenv("MISTRAL_API_ENDPOINT")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")