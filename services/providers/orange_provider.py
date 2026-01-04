import requests
import base64
import os
from services.constants import PaymentStatus


class OrangeProvider:

    ORANGE_STATUS_MAP = {
        "SUCCESS": PaymentStatus.VALIDE.value,
        "PENDING": PaymentStatus.EN_ATTENTE.value,
        "FAILED": PaymentStatus.ECHOUE.value,
        "CANCELLED": PaymentStatus.ECHOUE.value,
        "EXPIRED": PaymentStatus.ECHOUE.value,
    }

    def __init__(self):
        self.client_id = os.getenv("ORANGE_CLIENT_ID")
        self.client_secret = os.getenv("ORANGE_CLIENT_SECRET")

        # ✅ ORANGE SONATEL SANDBOX
        self.oauth_url = "https://api.sandbox.orange-sonatel.com/oauth/token"
        self.webpay_url = (
            "https://api.sandbox.orange-sonatel.com/"
            "orange-money-webpay/dev/v1/webpayment"
        )

    # --------------------------------------------------
    # 🔐 OAuth Token
    # --------------------------------------------------
    def get_access_token(self):
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        data = {"grant_type": "client_credentials"}

        r = requests.post(self.oauth_url, headers=headers, data=data, timeout=10)
        r.raise_for_status()

        return r.json()["access_token"]

    # --------------------------------------------------
    # 💳 INIT WEB PAYMENT
    # --------------------------------------------------
    def init_payment(self, amount, reference, return_url):
        token = self.get_access_token()

        payload = {
            "merchant_key": "TEST",
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

        r = requests.post(
            self.webpay_url,
            json=payload,
            headers=headers,
            timeout=10
        )
        r.raise_for_status()

        data = r.json()

        return {
            "payment_url": data.get("payment_url") or data.get("redirect_url")
        }
    
    # --------------------------------------------------
    # 🔁 CALLBACK
    # --------------------------------------------------
    def map_status(self, orange_status: str) -> str:
        status = self.ORANGE_STATUS_MAP.get(orange_status)
        if not status:
            raise ValueError(f"Statut Orange inconnu : {orange_status}")
        return status
