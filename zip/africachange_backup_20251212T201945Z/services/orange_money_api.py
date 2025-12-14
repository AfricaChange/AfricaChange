import requests
import os
import base64

class OrangeMoneyAPI:
    def __init__(self):
        self.client_id = os.getenv("ORANGE_CLIENT_ID")
        self.client_secret = os.getenv("ORANGE_CLIENT_SECRET")
        self.merchant_key = os.getenv("ORANGE_MERCHANT_KEY")
        self.currency = os.getenv("ORANGE_CURRENCY", "XOF")

        # URLs officielles Orange Money Sandbox
        self.token_url = "https://api.orange.com/oauth/v3/token"
        self.payment_url = "https://api.orange.com/orange-money-webpay/dev/v1/webpayment"
        self.status_url = "https://api.orange.com/orange-money-webpay/dev/v1/paymentstatus"

    # --------------------------------------------------
    # 1) Obtenir le token correctement (réparé)
    # --------------------------------------------------
    def get_token(self):
        # Encodage Base64 : client_id:client_secret
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_base64 = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_base64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {"grant_type": "client_credentials"}

        r = requests.post(self.token_url, headers=headers, data=data)

        if r.status_code != 200:
            print("Erreur Token:", r.text)
            return None

        return r.json().get("access_token")

    # --------------------------------------------------
    # 2) Initialisation du paiement
    # --------------------------------------------------
    def init_payment(self, amount, phone_number, return_url, reference):
        token = self.get_token()
        if not token:
            return {"success": False, "error": "Impossible d’obtenir le token"}

        payload = {
            "merchant_key": self.merchant_key,
            "currency": self.currency,
            "order_id": reference,
            "amount": str(amount),
            "return_url": return_url,
            "payer_phone": phone_number
        }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        r = requests.post(self.payment_url, headers=headers, json=payload)

        if r.status_code == 201:
            return {
                "success": True,
                "data": {
                    "payment_url": r.json().get("payment_url"),
                    "reference": reference
                }
            }

        return {"success": False, "error": r.text}

    # --------------------------------------------------
    # 3) Vérification de paiement
    # --------------------------------------------------
    def check_payment_status(self, order_id):
        token = self.get_token()
        if not token:
            return {"success": False, "error": "Token invalide"}

        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.status_url}/{order_id}"

        r = requests.get(url, headers=headers)

        if r.status_code != 200:
            return {"success": False, "error": r.text}

        return {"success": True, "data": r.json()}
