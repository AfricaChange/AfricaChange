from __future__ import annotations

from dataclasses import dataclass

from models import Parametre, Rate


@dataclass(frozen=True)
class CorridorMetadata:
    country_code: str
    country_name: str
    flag: str
    currency_code: str


_CURRENCY_METADATA: dict[str, CorridorMetadata] = {
    "XOF": CorridorMetadata("SN", "Senegal", "🇸🇳", "XOF"),
    "CFA": CorridorMetadata("SN", "Senegal", "🇸🇳", "CFA"),
    "GNF": CorridorMetadata("GN", "Guinee", "🇬🇳", "GNF"),
    "EUR": CorridorMetadata("FR", "France", "🇫🇷", "EUR"),
    "USD": CorridorMetadata("US", "Etats-Unis", "🇺🇸", "USD"),
}

DEFAULT_DEMO_AMOUNT = 5000.0


def _metadata_for_currency(currency_code: str) -> CorridorMetadata:
    normalized = (currency_code or "").upper()
    return _CURRENCY_METADATA.get(
        normalized,
        CorridorMetadata(
            country_code=normalized,
            country_name=normalized,
            flag="",
            currency_code=normalized,
        ),
    )


def _preferred_corridor_key(rate: Rate) -> tuple[int, str]:
    ranking = {
        ("XOF", "GNF"): 0,
        ("CFA", "GNF"): 1,
        ("GNF", "XOF"): 2,
        ("GNF", "CFA"): 3,
    }
    return ranking.get((rate.from_currency, rate.to_currency), 100), f"{rate.from_currency}->{rate.to_currency}"


def list_supported_corridors() -> list[dict[str, object]]:
    rates = Rate.query.order_by(Rate.from_currency.asc(), Rate.to_currency.asc()).all()
    corridors: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()

    for rate in rates:
        pair = (rate.from_currency, rate.to_currency)
        if pair in seen or rate.from_currency == rate.to_currency:
            continue
        seen.add(pair)

        source = _metadata_for_currency(rate.from_currency)
        target = _metadata_for_currency(rate.to_currency)
        corridors.append(
            {
                "from_currency": rate.from_currency,
                "to_currency": rate.to_currency,
                "from_country_code": source.country_code,
                "from_country_name": source.country_name,
                "from_flag": source.flag,
                "to_country_code": target.country_code,
                "to_country_name": target.country_name,
                "to_flag": target.flag,
                "corridor_key": f"{rate.from_currency}->{rate.to_currency}",
            }
        )

    corridors.sort(key=lambda corridor: _preferred_corridor_key_obj(corridor))
    return corridors


def _preferred_corridor_key_obj(corridor: dict[str, object]) -> tuple[int, str]:
    ranking = {
        ("XOF", "GNF"): 0,
        ("CFA", "GNF"): 1,
        ("GNF", "XOF"): 2,
        ("GNF", "CFA"): 3,
    }
    from_currency = str(corridor["from_currency"])
    to_currency = str(corridor["to_currency"])
    return ranking.get((from_currency, to_currency), 100), f"{from_currency}->{to_currency}"


def default_corridor() -> dict[str, object] | None:
    corridors = list_supported_corridors()
    return corridors[0] if corridors else None


def build_quote(
    *,
    amount: float,
    from_currency: str,
    to_currency: str,
) -> dict[str, object]:
    source = _metadata_for_currency(from_currency)
    target = _metadata_for_currency(to_currency)
    corridor_key = f"{from_currency}->{to_currency}"

    try:
        parsed_amount = float(amount)
    except (TypeError, ValueError):
        parsed_amount = 0.0

    if parsed_amount <= 0:
        return {
            "ok": False,
            "error_code": "invalid_amount",
            "error_message": "Montant invalide",
            "corridor_key": corridor_key,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "from_country_code": source.country_code,
            "from_country_name": source.country_name,
            "from_flag": source.flag,
            "to_country_code": target.country_code,
            "to_country_name": target.country_name,
            "to_flag": target.flag,
        }

    rate = Rate.query.filter_by(
        from_currency=from_currency,
        to_currency=to_currency,
    ).first()

    if not rate:
        return {
            "ok": False,
            "error_code": "corridor_unavailable",
            "error_message": "Ce corridor n'est pas encore disponible.",
            "corridor_key": corridor_key,
            "from_currency": from_currency,
            "to_currency": to_currency,
            "from_country_code": source.country_code,
            "from_country_name": source.country_name,
            "from_flag": source.flag,
            "to_country_code": target.country_code,
            "to_country_name": target.country_name,
            "to_flag": target.flag,
        }

    target_amount = round(parsed_amount * float(rate.rate), 2)

    return {
        "ok": True,
        "corridor_key": corridor_key,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "from_country_code": source.country_code,
        "from_country_name": source.country_name,
        "from_flag": source.flag,
        "to_country_code": target.country_code,
        "to_country_name": target.country_name,
        "to_flag": target.flag,
        "amount_sent": parsed_amount,
        "amount_received": target_amount,
        "rate": float(rate.rate),
        "fee_known": False,
        "fee_label": _fee_label_from_configuration(),
    }


def build_demo_quote() -> dict[str, object]:
    source = _metadata_for_currency("XOF")
    target = _metadata_for_currency("GNF")
    return {
        "ok": False,
        "error_code": "rates_unavailable",
        "error_message": "Impossible de recuperer le taux pour le moment.",
        "corridor_key": "XOF->GNF",
        "from_currency": source.currency_code,
        "to_currency": target.currency_code,
        "from_country_code": source.country_code,
        "from_country_name": source.country_name,
        "from_flag": source.flag,
        "to_country_code": target.country_code,
        "to_country_name": target.country_name,
        "to_flag": target.flag,
        "amount_sent": DEFAULT_DEMO_AMOUNT,
        "amount_received": None,
        "rate": None,
        "fee_known": False,
        "fee_label": _fee_label_from_configuration(),
    }


def _fee_label_from_configuration() -> str:
    param = Parametre.query.filter_by(cle="platform_fee_rate").first()
    try:
        fee_rate = float(param.valeur) if param and param.valeur is not None else None
    except (TypeError, ValueError):
        fee_rate = None

    if fee_rate is None:
        return "Frais calcules a l'etape suivante"

    return "Frais calcules a l'etape suivante"
