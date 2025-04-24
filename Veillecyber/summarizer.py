from mistralai import Mistral
from config import MISTRAL_API_KEY

def summarize_text(text):
    model = "mistral-large-latest"
    client = Mistral(api_key=MISTRAL_API_KEY)
    chat_response = client.chat.complete(
        model=model,
        messages = [
            {
                "role": "user",
                "content": (
                    "Tu es une IA spécialisée en cybersécurité et en intelligence artificielle. "
                    "Voici un article de presse scrappé automatiquement sur ces thématiques. "
                    "Fais un résumé clair, concis et professionnel, en **français**, en moins de 15 lignes. "
                    "Fais ressortir les points essentiels : le sujet principal, les acteurs impliqués, les conséquences, et les faits marquants. "
                    "Ignore les phrases promotionnelles ou vagues. S’il s’agit d’un contenu peu informatif, conclus simplement par : "
                    "\"Contenu promotionnel ou peu informatif.\"\n\n"
                    f"{text}"
                )
            }
        ]
    )
    return chat_response.choices[0].message.content