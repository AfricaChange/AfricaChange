import requests
import base64
import os


class OrangeProvider:

    def __init__(self):
        self.client_id = os.getenv("ORANGE_CLIENT_ID")
        self.client_secret = os.getenv("ORANGE_CLIENT_SECRET")

        # ✅ SANDBOX ORANGE SONATEL
        self.oauth_url = "https://api.sandbox.orange-sonatel.com/oauth/token"
        self.payment_url = (
            "https://api.sandbox.orange-sonatel.com/"
            "orange-money-webpay/dev/v1/webpayment"
        )

    # --------------------------------------------------
    # 🔐 OAuth Token
    # --------------------------------------------------
    def get_access_token(self):
        if not self.client_id or not self.client_secret:
            raise Exception("ORANGE_CLIENT_ID ou ORANGE_CLIENT_SECRET manquant")

        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        data = {
            "grant_type": "client_credentials"
        }

        r = requests.post(self.oauth_url, headers=headers, data=data, timeout=15)

        if r.status_code != 200:
            raise Exception(
                f"OAuth Orange échoué ({r.status_code}) : {r.text}"
            )

        return r.json()["access_token"]

    # --------------------------------------------------
    # 💳 INIT PAYMENT
    # --------------------------------------------------
    def init_payment(self, amount, phone, reference, return_url):
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
            timeout=15
        )

        if r.status_code not in (200, 201):
            raise Exception(
                f"Init paiement Orange échoué ({r.status_code}) : {r.text}"
            )

        data = r.json()

        return {
            "payment_url": data.get("payment_url")
                or data.get("redirect_url")
        }

    # --------------------------------------------------
    def verify_callback(self, raw_payload, headers):
        return True

    def is_valid_status(self, payload):
        return payload.get("status") in ("SUCCESS", "FAILED")
