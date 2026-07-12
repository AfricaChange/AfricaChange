from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from engines.profitability_engine.enums import ProfitabilityLevel


def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


@dataclass(frozen=True)
class ProfitabilityInput:
    conversion_reference: str
    devise_reference: str
    montant_source_client: Decimal
    montant_destination_client: Decimal
    taux_client: Decimal
    marge_estimee: Decimal
    cout_liquidite_estime: Decimal
    cout_liquidite_reel: Decimal
    frais_payin_reels: Decimal = Decimal("0")
    frais_payout_reels: Decimal = Decimal("0")
    frais_marchand_reels: Decimal = Decimal("0")
    autres_couts_reels: Decimal = Decimal("0")
    commissions_client: Decimal = Decimal("0")
    commissions_marchand: Decimal = Decimal("0")
    mode_execution: str = ""
    provider_code: str = ""
    corridor: str = ""
    segment_client: str = "standard"
    classification_flux: str = "ponctuel"
    provisoire: bool = False
    annulee: bool = False
    remboursee: bool = False

    def __post_init__(self):
        for field_name in (
            "montant_source_client",
            "montant_destination_client",
            "taux_client",
            "marge_estimee",
            "cout_liquidite_estime",
            "cout_liquidite_reel",
            "frais_payin_reels",
            "frais_payout_reels",
            "frais_marchand_reels",
            "autres_couts_reels",
            "commissions_client",
            "commissions_marchand",
        ):
            object.__setattr__(self, field_name, _to_decimal(getattr(self, field_name)))


@dataclass(frozen=True)
class ProfitabilityResult:
    revenu_brut: Decimal
    cout_total_estime: Decimal
    cout_total_reel: Decimal
    marge_brute_estimee: Decimal
    marge_brute_reelle: Decimal
    marge_nette_reelle: Decimal
    ecart_prevision_reel: Decimal
    taux_marge_nette: Decimal
    profitable: bool
    niveau_rentabilite: ProfitabilityLevel
    motif: str
    calculated_at: datetime
    provisoire: bool = False

    def __post_init__(self):
        for field_name in (
            "revenu_brut",
            "cout_total_estime",
            "cout_total_reel",
            "marge_brute_estimee",
            "marge_brute_reelle",
            "marge_nette_reelle",
            "ecart_prevision_reel",
            "taux_marge_nette",
        ):
            object.__setattr__(self, field_name, _to_decimal(getattr(self, field_name)))
