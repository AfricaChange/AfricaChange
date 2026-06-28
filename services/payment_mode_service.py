from database import db
from models import Parametre


class PaymentModeService:
    PARAM_KEY = "payment_mode"
    API = "api"
    MANUAL = "manuel"
    SIMULATION = "simulation"
    ALLOWED_MODES = {API, MANUAL, SIMULATION}

    @staticmethod
    def get_mode() -> str:
        param = Parametre.query.filter_by(cle=PaymentModeService.PARAM_KEY).first()
        value = (param.valeur.strip().lower() if param and param.valeur else PaymentModeService.API)
        if value not in PaymentModeService.ALLOWED_MODES:
            return PaymentModeService.API
        return value

    @staticmethod
    def set_mode(mode: str) -> str:
        normalized = (mode or "").strip().lower()
        if normalized not in PaymentModeService.ALLOWED_MODES:
            raise ValueError("Mode de paiement invalide")

        param = Parametre.query.filter_by(cle=PaymentModeService.PARAM_KEY).first()
        if not param:
            param = Parametre(cle=PaymentModeService.PARAM_KEY)
            db.session.add(param)
        param.valeur = normalized
        return normalized
