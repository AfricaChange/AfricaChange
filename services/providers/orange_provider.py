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

        if not self.client_id or not self.client_secret:
            raise RuntimeError("Clés Orange manquantes")

        # ✅ SANDBOX SONATEL
        self.oauth_url = "https://api.sandbox.orange-sonatel.com/oauth/token"
        self.payment_url = (
            "https://api.sandbox.orange-sonatel.com/"
            "orange-money-webpay/dev/v1/webpayment"
        )

    # --------------------------------------------------
    # 🔐 TOKEN OAUTH
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

        r = requests.post(self.oauth_url, headers=headers, data=data, timeout=15)

        if r.status_code != 200:
            raise RuntimeError(
                f"Orange OAuth error {r.status_code} : {r.text}"
            )

        return r.json()["access_token"]

    # --------------------------------------------------
    # 💳 INIT PAIEMENT
    # --------------------------------------------------
    def init_payment(self, *, amount, reference, return_url):
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
            self.payment_url,
            json=payload,
            headers=headers,
            timeout=20
        )

        if r.status_code not in (200, 201):
            raise RuntimeError(
                f"Orange init error {r.status_code} : {r.text}"
            )

        data = r.json()

        return {
            "payment_url": data.get("payment_url")
                or data.get("redirect_url")
        }

    # --------------------------------------------------
    # 🔁 CALLBACK
    # --------------------------------------------------
    def map_status(self, orange_status: str) -> str:
        status = self.ORANGE_STATUS_MAP.get(orange_status)
        if not status:
            raise ValueError(f"Statut Orange inconnu : {orange_status}")
        return status
