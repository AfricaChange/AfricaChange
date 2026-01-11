import requests
import base64
import os

class OrangeProvider:

    def __init__(self):
        self.client_id = os.getenv("ORANGE_CLIENT_ID")
        self.client_secret = os.getenv("ORANGE_CLIENT_SECRET")
        self.oauth_url = "https://api.sandbox.orange-sonatel.com/oauth/token"
        self.payment_url = ""

    def get_access_token(self):
        import base64, requests

        creds = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(creds.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        r = requests.post(
            self.oauth_url,
            headers=headers,
            data={"grant_type": "client_credentials"},
            timeout=10
        )
        r.raise_for_status()
        return r.json()["access_token"]

    def init_payment(self, amount, phone, reference):
        token = self.get_access_token()

        url = "https://api.sandbox.orange-sonatel.com/api/eWallet/v1/payments"

        payload = {
            "amount": amount,
            "currency": "XOF",
            "externalId": reference,
            "payer": {
                "partyIdType": "MSISDN",
                "partyId": phone
            },
            "payeeNote": "AfricaChange paiement",
            "payerMessage": "Confirmez le paiement"
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        r = requests.post(url, json=payload, headers=headers, timeout=10)
        r.raise_for_status()

        return {"status": "PENDING"}
 