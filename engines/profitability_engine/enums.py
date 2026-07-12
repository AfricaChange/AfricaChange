from enum import Enum


class ProfitabilityLevel(str, Enum):
    PERTE = "perte"
    CRITIQUE = "critique"
    FAIBLE = "faible"
    ACCEPTABLE = "acceptable"
    BONNE = "bonne"
    EXCELLENTE = "excellente"
