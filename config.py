import os
from dotenv import load_dotenv

load_dotenv()  # Charge les variables depuis .env

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")

    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Orange Money
    OM_API_KEY = os.getenv("OM_API_KEY")
    OM_CLIENT_ID = os.getenv("OM_CLIENT_ID")
    OM_CLIENT_SECRET = os.getenv("OM_CLIENT_SECRET")
    OM_MERCHANT_KEY = os.getenv("OM_MERCHANT_KEY")
    OM_COUNTRY = os.getenv("OM_COUNTRY")
    OM_CURRENCY = os.getenv("OM_CURRENCY")

    # MTN MoMo
    MTN_API_KEY = os.getenv("MTN_API_KEY")
    MTN_USER_ID = os.getenv("MTN_USER_ID")
    MTN_PRIMARY_KEY = os.getenv("MTN_PRIMARY_KEY")
    MTN_ENVIRONMENT = os.getenv("MTN_ENVIRONMENT")

    # Paydunya
    PAYDUNYA_MASTER_KEY = os.getenv("PAYDUNYA_MASTER_KEY")
    PAYDUNYA_PRIVATE_KEY = os.getenv("PAYDUNYA_PRIVATE_KEY")
    PAYDUNYA_TOKEN = os.getenv("PAYDUNYA_TOKEN")
    PAYDUNYA_MODE = os.getenv("PAYDUNYA_MODE")
