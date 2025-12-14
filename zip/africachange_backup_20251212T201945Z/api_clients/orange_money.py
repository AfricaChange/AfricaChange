import requests
import uuid
from config import Config


class OrangeMoneyAPI:

    def __init__(self):
        self.api_key = Config.OM_API_KEY
        self.client_id = Config.OM_CLIENT_ID
        self.client_secret = Config.OM_CLIENT_SECRET
        self.merchant_key = Config.OM_MERCHANT_KEY
        self.country = Config.OM_COUNTRY
        self.currency = Config.OM_CURRENCY

        self.base_url = "https://api.orange.com/orange-money-webpay/dev"

    # 🔹 1. Obtenir un token OAuth 2.0
    def get_token(self):
        url = "https://api.orange.com/oauth/v3/token"

        response = requests.post(
            url,
            data={"grant_type": "client_credentials"},
            auth=(self.client_id, self.client_secret)
        )

        if response.status_code != 200:
            raise Exception(f"Erreur Token Orange : {response.text}")

        return response.json()["access_token"]

    # 🔹 2. Initier un paiement
    def init_payment(self, amount, phone_number, return_url):
        token = self.get_token()

        reference = str(uuid.uuid4())[:12]

        payload = {
            "merchant_key": self.merchant_key,
            "amount": int(amount),
            "currency": self.currency,
            "order_id": reference,
            "return_url": return_url,
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Orange-Money-Phone": phone_number,
            "Content-Type": "application/json"
        }

        url = f"{self.base_url}/init"

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print("Erreur init_payment OM :", response.text)
            return {"success": False, "error": response.text}

        data = response.json()
        data["reference"] = reference

        return {"success": True, "data": data}

    # 🔹 3. Vérifier le statut du paiement
    def check_payment_status(self, reference):
        token = self.get_token()

        url = f"{self.base_url}/paymentStatus/{reference}"

        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            return {"success": False, "error": response.text}

        return {"success": True, "data": response.json()}
