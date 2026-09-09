import logging

from mistralai import Mistral

from config import MISTRAL_API_KEY

MODEL = "mistral-large-latest"

PROMPT = (
    "Tu es une IA spécialisée en cybersécurité et en intelligence artificielle. "
    "Voici un article de presse scrappé automatiquement sur ces thématiques. "
    "Fais un résumé clair, concis et professionnel, en **français**, en moins de 15 lignes. "
    "Fais ressortir les points essentiels : le sujet principal, les acteurs impliqués, "
    "les conséquences, et les faits marquants. "
    "Ignore les phrases promotionnelles ou vagues. S'il s'agit d'un contenu peu informatif, "
    "conclus simplement par : \"Contenu promotionnel ou peu informatif.\"\n\n"
)


def summarize_text(text):
    """Résume un texte via l'API Mistral. Renvoie None en cas d'échec."""
    if not MISTRAL_API_KEY:
        logging.error("MISTRAL_API_KEY manquant — résumé impossible.")
        return None
    try:
        client = Mistral(api_key=MISTRAL_API_KEY)
        chat_response = client.chat.complete(
            model=MODEL,
            messages=[{"role": "user", "content": PROMPT + text}],
        )
        return chat_response.choices[0].message.content
    except Exception as exc:
        logging.error(f"Échec de l'appel Mistral : {exc}")
        return None
