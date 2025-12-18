import os
import requests
import base64

class OrangeProvider:

    TOKEN_URL = "https://api.orange.com/oauth/v3/token"
    PAYMENT_URL = "https://api.orange.com/orange-money-webpay/dev/v1/webpayment"
    STATUS_URL = "https://api.orange.com/orange-money-webpay/dev/v1/paymentstatus"

    def __init__(self):
        self.client_id = os.getenv("ORANGE_CLIENT_ID")
        self.client_secret = os.getenv("ORANGE_CLIENT_SECRET")
        self.merchant_key = os.getenv("ORANGE_MERCHANT_KEY")
        self.currency = os.getenv("ORANGE_CURRENCY", "XOF")

        if not all([self.client_id, self.client_secret, self.merchant_key]):
            raise RuntimeError("Clés Orange Money manquantes")

    # --------------------------------------------------
    # 🔑 TOKEN (simple + safe)
    # --------------------------------------------------
    def _get_token(self):
        auth = f"{self.client_id}:{self.client_secret}"
        auth_base64 = base64.b64encode(auth.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {"grant_type": "client_credentials"}

        r = requests.post(self.TOKEN_URL, headers=headers, data=data, timeout=10)

        if r.status_code != 200:
            raise RuntimeError("Impossible d’obtenir le token Orange")

        return r.json().get("access_token")

    # --------------------------------------------------
    # 💳 INIT PAYMENT
    # --------------------------------------------------
    def init_payment(self, *, amount, phone, reference, return_url):
        token = self._get_token()

        payload = {
            "merchant_key": self.merchant_key,
            "currency": self.currency,
            "order_id": reference,   # 🔐 référence DB
            "amount": str(int(amount)),
            "return_url": return_url,
            "payer_phone": phone
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        r = requests.post(
            self.PAYMENT_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        if r.status_code != 201:
            raise RuntimeError(f"Erreur Orange Money: {r.text}")

        return {
            "payment_url": r.json().get("payment_url"),
            "provider_reference": reference
        }

    # --------------------------------------------------
    # 🔎 CHECK STATUS (CALLBACK SAFE)
    # --------------------------------------------------
    def check_status(self, reference):
        token = self._get_token()

        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.STATUS_URL}/{reference}"

        r = requests.get(url, headers=headers, timeout=10)

        if r.status_code != 200:
            raise RuntimeError("Erreur vérification Orange")

        return r.json()
