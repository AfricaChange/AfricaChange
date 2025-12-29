# services/constants.py

from enum import Enum

class PaymentStatus(str, Enum):
    EN_ATTENTE = "en_attente"
    EN_COURS = "paiement_en_cours"
    VALIDE = "valide"
    ECHOUE = "echoue"
    BLOQUE = "bloque"
    REMBOURSE = "rembourse"
