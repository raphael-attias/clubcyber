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
                "content": f"Fais un résumé concis de ce texte :\n\n{text}",
            },
        ]
    )
    return chat_response.choices[0].message.content