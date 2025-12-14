from mailjet_rest import Client
import os

api_key = os.getenv("MAILJET_API_KEY")
api_secret = os.getenv("MAILJET_SECRET_KEY")
sender_email = os.getenv("MAILJET_SENDER_EMAIL")
sender_name = os.getenv("MAILJET_SENDER_NAME")

mailjet = Client(auth=(api_key, api_secret), version='v3.1')



def send_reset_email(to_email, reset_link):
    data = {
      'Messages': [
        {
          "From": {
            "Email": sender_email,
            "Name": sender_name
          },
          "To": [
            {
              "Email": to_email
            }
          ],
          "Subject": "Réinitialisation de votre mot de passe - AfricaChange",
          "HTMLPart": f"""
          <h3>Bonjour,</h3>
          <p>Vous avez demandé la réinitialisation de votre mot de passe.</p>
          <p>Cliquez sur ce lien pour choisir un nouveau mot de passe :</p>
          <a href="{reset_link}">{reset_link}</a>
          <p>Si vous n'avez pas demandé cela, ignorez cet email.</p>
          <p><strong>AfricaChange</strong></p>
          """
        }
      ]
    }
    
    result = mailjet.send.create(data=data)
    print(result.status_code, result.json())
