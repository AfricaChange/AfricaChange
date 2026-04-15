from flask import Blueprint, request
import requests

webhook_bp = Blueprint("webhook", __name__)

VERIFY_TOKEN = "africachange_token"

ACCESS_TOKEN ="EAAXtyblg5oUBRL3ZCZBLCwH7YSg8ub5Joju3WCAY90DzwkJnlbQnJPLMl5KxnJiLZBgzKcEeom32FsXvumhxEZCU233JggvkDj161fLU4MUOpiYsoXSSpZAN6SyZArxoA8IUTPuaaQJBqANrmZA2x9nuHZBTicLgThw9XO4TBI4Vk3CkmuWZBDwznl4wOblt8cmW9LxAVrvfejLmsmM49UgkMMHMFUiciItO43aZAaw3hYZCZBpsqqKx0qEx47DTj8MafMBwdshSFWGZBnwsjNfqDNYywtraKPQZDZD"
PHONE_NUMBER_ID ="224611710542"


@webhook_bp.route("/webhook", methods=["GET", "POST"])
def whatsapp_webhook():

    # Vérification Meta
    if request.method == "GET":
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if token == VERIFY_TOKEN:
            return challenge
        return "Token invalide", 403

    # Réception message
    if request.method == "POST":
        data = request.get_json()

        try:
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            numero = message["from"]
            texte = message["text"]["body"]

            print(f"📩 {numero}: {texte}")

            # 🔥 réponse automatique
            envoyer_message(numero, reponse_bot(texte))

        except Exception as e:
            print("Erreur:", e)

        return "OK", 200


# 🔥 fonction réponse intelligente
def reponse_bot(message):
    message = message.lower()

    if "bonjour" in message:
        return "Bienvenue sur AfricaChangeX 💱\nEnvoyez le montant à convertir (CFA ↔ GNF)"

    if message.isdigit():
        return f"Vous voulez convertir {message} ?\nVeuillez envoyer votre preuve de paiement."

    return "Je n’ai pas compris 🤖\nTapez 'bonjour' pour commencer."


# 🔥 fonction envoi WhatsApp
def envoyer_message(numero, texte):

    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "text",
        "text": {
            "body": texte
        }
    }

    requests.post(url, headers=headers, json=data)