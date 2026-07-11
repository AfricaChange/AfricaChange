from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List


def _to_decimal(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None or value == "":
        return Decimal("0")
    return Decimal(str(value))


@dataclass(frozen=True)
class ReportingInputRow:
    conversion_reference: str
    corridor: str
    merchant_id: int = 0
    merchant_code: str = ""
    merchant_nom: str = ""
    client_reference: str = ""
    client_nom: str = ""
    segment_client: str = "standard"
    classification_flux: str = "ponctuel"
    devise_source: str = ""
    devise_cible: str = ""
    execution_mode: str = ""
    liquidity_source_type: str = ""
    provider_code: str = ""
    statut: str = ""
    montant_source: Decimal = Decimal("0")
    montant_destination: Decimal = Decimal("0")
    revenu_brut: Decimal = Decimal("0")
    marge_estimee: Decimal = Decimal("0")
    marge_nette: Decimal = Decimal("0")
    ecart_prevision_reel: Decimal = Decimal("0")
    execution_cost: Decimal = Decimal("0")
    provider_fees: Decimal = Decimal("0")
    delai_execution_minutes: Decimal = Decimal("0")
    profitable: bool = False
    incident: bool = False
    provisoire: bool = False
    sous_prevision: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        for field_name in (
            "montant_source",
            "montant_destination",
            "revenu_brut",
            "marge_estimee",
            "marge_nette",
            "ecart_prevision_reel",
            "execution_cost",
            "provider_fees",
            "delai_execution_minutes",
        ):
            object.__setattr__(self, field_name, _to_decimal(getattr(self, field_name)))


@dataclass(frozen=True)
class CorridorReportRow:
    corridor: str
    conversions_count: int
    profitable_count: int
    volume_source: Decimal
    volume_destination: Decimal
    revenu_brut: Decimal
    marge_nette: Decimal
    taux_marge: Decimal

    def __post_init__(self):
        for field_name in ("volume_source", "volume_destination", "revenu_brut", "marge_nette", "taux_marge"):
            object.__setattr__(self, field_name, _to_decimal(getattr(self, field_name)))


@dataclass(frozen=True)
class MerchantReportRow:
    merchant_code: str
    merchant_nom: str
    conversions_count: int
    volume_destination: Decimal
    marge_nette: Decimal
    taux_marge: Decimal
    delai_moyen_minutes: Decimal
    incidents_count: int
    score: str

    def __post_init__(self):
        for field_name in ("volume_destination", "marge_nette", "taux_marge", "delai_moyen_minutes"):
            object.__setattr__(self, field_name, _to_decimal(getattr(self, field_name)))


@dataclass(frozen=True)
class ClientReportRow:
    client_reference: str
    client_nom: str
    segment_client: str
    conversions_count: int
    volume_source: Decimal
    volume_destination: Decimal
    marge_nette: Decimal
    frequence: str
    classification_dominante: str

    def __post_init__(self):
        for field_name in ("volume_source", "volume_destination", "marge_nette"):
            object.__setattr__(self, field_name, _to_decimal(getattr(self, field_name)))


@dataclass(frozen=True)
class CurrencyReportRow:
    currency_code: str
    conversions_count: int
    volume_source: Decimal
    volume_destination: Decimal
    marge_nette: Decimal
    execution_cost: Decimal

    def __post_init__(self):
        for field_name in ("volume_source", "volume_destination", "marge_nette", "execution_cost"):
            object.__setattr__(self, field_name, _to_decimal(getattr(self, field_name)))


@dataclass(frozen=True)
class ExecutionModeReportRow:
    execution_mode: str
    conversions_count: int
    profitable_count: int
    volume_destination: Decimal
    marge_nette: Decimal
    taux_marge: Decimal
    provider_fees: Decimal
    execution_cost: Decimal

    def __post_init__(self):
        for field_name in ("volume_destination", "marge_nette", "taux_marge", "provider_fees", "execution_cost"):
            object.__setattr__(self, field_name, _to_decimal(getattr(self, field_name)))


@dataclass(frozen=True)
class SegmentReportRow:
    segment_client: str
    conversions_count: int
    profitable_count: int
    volume_destination: Decimal
    marge_nette: Decimal
    taux_marge: Decimal

    def __post_init__(self):
        for field_name in ("volume_destination", "marge_nette", "taux_marge"):
            object.__setattr__(self, field_name, _to_decimal(getattr(self, field_name)))


@dataclass(frozen=True)
class ReportingSnapshot:
    corridor_rows: List[CorridorReportRow]
    merchant_rows: List[MerchantReportRow]
    client_rows: List[ClientReportRow]
    currency_rows: List[CurrencyReportRow]
    execution_mode_rows: List[ExecutionModeReportRow]
    segment_rows: List[SegmentReportRow]
    generated_at: datetime = field(default_factory=datetime.utcnow)
