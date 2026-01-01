import requests
import base64
import os
from datetime import datetime


class OrangeProvider:

    def __init__(self):
        self.env = os.getenv("ORANGE_ENV", "sandbox")
        self.client_id = os.getenv("ORANGE_CLIENT_ID")
        self.client_secret = os.getenv("ORANGE_CLIENT_SECRET")

        self.base_url = "https://api.orange.com"

    # --------------------------------------------------
    # 🔐 OAuth Token
    # --------------------------------------------------
    def get_access_token(self):
        token_url = f"{self.base_url}/oauth/v3/token"

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        data = {"grant_type": "client_credentials"}

        r = requests.post(token_url, headers=headers, data=data, timeout=10)
        r.raise_for_status()

        return r.json()["access_token"]

    # --------------------------------------------------
    # 💳 INIT PAYMENT (SANDBOX)
    # --------------------------------------------------
    def init_payment(self, amount, phone, reference, return_url):
        token = self.get_access_token()

        url = f"{self.base_url}/orange-money-webpay/dev/v1/webpayment"

        payload = {
            "merchant_key": "TEST",  # sandbox accepte une valeur fictive
            "currency": "XOF",
            "order_id": reference,
            "amount": int(amount),
            "return_url": return_url,
            "cancel_url": return_url,
            "notif_url": return_url,
            "lang": "fr",
            "reference": reference,
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()

        data = r.json()

        return {
            "payment_url": data.get("payment_url") or data.get("redirect_url")
        }

    # --------------------------------------------------
    # 🔐 CALLBACK VERIFICATION
    # --------------------------------------------------
    def verify_callback(self, raw_payload, headers):
        # Sandbox : signature souvent absente
        return True

    def extract_nonce(self, payload, headers):
        return payload.get("order_id")

    def is_valid_status(self, payload):
        return payload.get("status") in ("SUCCESS", "FAILED")
