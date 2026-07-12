from collections import Counter, defaultdict
from decimal import Decimal

from engines.reporting_engine.models import (
    ClientReportRow,
    CorridorReportRow,
    CurrencyReportRow,
    ExecutionModeReportRow,
    MerchantReportRow,
    ReportingSnapshot,
    SegmentReportRow,
)


class ReportingEngine:
    @staticmethod
    def generer(rows):
        return ReportingSnapshot(
            corridor_rows=ReportingEngine._aggregate_corridors(rows),
            merchant_rows=ReportingEngine._aggregate_merchants(rows),
            client_rows=ReportingEngine._aggregate_clients(rows),
            currency_rows=ReportingEngine._aggregate_currencies(rows),
            execution_mode_rows=ReportingEngine._aggregate_execution_modes(rows),
            segment_rows=ReportingEngine._aggregate_segments(rows),
        )

    @staticmethod
    def _aggregate_corridors(rows):
        grouped = defaultdict(list)
        for row in rows:
            grouped[row.corridor].append(row)

        results = []
        for corridor, items in grouped.items():
            revenu = sum((item.revenu_brut for item in items), Decimal("0"))
            marge = sum((item.marge_nette for item in items), Decimal("0"))
            results.append(
                CorridorReportRow(
                    corridor=corridor,
                    conversions_count=len(items),
                    profitable_count=sum(1 for item in items if item.profitable),
                    volume_source=sum((item.montant_source for item in items), Decimal("0")),
                    volume_destination=sum((item.montant_destination for item in items), Decimal("0")),
                    revenu_brut=revenu,
                    marge_nette=marge,
                    taux_marge=ReportingEngine._safe_rate(marge, revenu),
                )
            )
        return sorted(results, key=lambda item: item.corridor)

    @staticmethod
    def _aggregate_merchants(rows):
        grouped = defaultdict(list)
        for row in rows:
            if row.merchant_code:
                grouped[(row.merchant_code, row.merchant_nom)].append(row)

        results = []
        for (merchant_code, merchant_nom), items in grouped.items():
            revenu = sum((item.revenu_brut for item in items), Decimal("0"))
            marge = sum((item.marge_nette for item in items), Decimal("0"))
            delai_total = sum((item.delai_execution_minutes for item in items), Decimal("0"))
            incidents_count = sum(1 for item in items if item.incident)
            delai_moyen = delai_total / Decimal(str(len(items))) if items else Decimal("0")
            taux = ReportingEngine._safe_rate(marge, revenu)
            results.append(
                MerchantReportRow(
                    merchant_code=merchant_code,
                    merchant_nom=merchant_nom,
                    conversions_count=len(items),
                    volume_destination=sum((item.montant_destination for item in items), Decimal("0")),
                    marge_nette=marge,
                    taux_marge=taux,
                    delai_moyen_minutes=delai_moyen,
                    incidents_count=incidents_count,
                    score=ReportingEngine._merchant_score(
                        taux_marge=taux,
                        incidents_count=incidents_count,
                        delai_moyen=delai_moyen,
                    ),
                )
            )
        return sorted(results, key=lambda item: item.merchant_code)

    @staticmethod
    def _aggregate_clients(rows):
        grouped = defaultdict(list)
        for row in rows:
            grouped[(row.client_reference, row.client_nom)].append(row)

        results = []
        for (client_reference, client_nom), items in grouped.items():
            classifications = Counter(item.classification_flux for item in items)
            segments = Counter(item.segment_client for item in items)
            results.append(
                ClientReportRow(
                    client_reference=client_reference,
                    client_nom=client_nom,
                    segment_client=segments.most_common(1)[0][0] if segments else "standard",
                    conversions_count=len(items),
                    volume_source=sum((item.montant_source for item in items), Decimal("0")),
                    volume_destination=sum((item.montant_destination for item in items), Decimal("0")),
                    marge_nette=sum((item.marge_nette for item in items), Decimal("0")),
                    frequence=ReportingEngine._frequency_label(len(items)),
                    classification_dominante=classifications.most_common(1)[0][0] if classifications else "ponctuel",
                )
            )
        return sorted(results, key=lambda item: (item.client_nom, item.client_reference))

    @staticmethod
    def _aggregate_currencies(rows):
        grouped = defaultdict(lambda: {
            "conversions_count": 0,
            "volume_source": Decimal("0"),
            "volume_destination": Decimal("0"),
            "marge_nette": Decimal("0"),
            "execution_cost": Decimal("0"),
        })

        for row in rows:
            source_bucket = grouped[row.devise_source]
            source_bucket["conversions_count"] += 1
            source_bucket["volume_source"] += row.montant_source
            source_bucket["marge_nette"] += row.marge_nette
            source_bucket["execution_cost"] += row.execution_cost

            target_bucket = grouped[row.devise_cible]
            target_bucket["conversions_count"] += 1
            target_bucket["volume_destination"] += row.montant_destination
            target_bucket["marge_nette"] += row.marge_nette
            target_bucket["execution_cost"] += row.execution_cost

        results = []
        for currency_code, values in grouped.items():
            results.append(
                CurrencyReportRow(
                    currency_code=currency_code,
                    conversions_count=values["conversions_count"],
                    volume_source=values["volume_source"],
                    volume_destination=values["volume_destination"],
                    marge_nette=values["marge_nette"],
                    execution_cost=values["execution_cost"],
                )
            )
        return sorted(results, key=lambda item: item.currency_code)

    @staticmethod
    def _aggregate_execution_modes(rows):
        grouped = defaultdict(list)
        for row in rows:
            grouped[row.execution_mode or "inconnu"].append(row)

        results = []
        for execution_mode, items in grouped.items():
            revenu = sum((item.revenu_brut for item in items), Decimal("0"))
            marge = sum((item.marge_nette for item in items), Decimal("0"))
            results.append(
                ExecutionModeReportRow(
                    execution_mode=execution_mode,
                    conversions_count=len(items),
                    profitable_count=sum(1 for item in items if item.profitable),
                    volume_destination=sum((item.montant_destination for item in items), Decimal("0")),
                    marge_nette=marge,
                    taux_marge=ReportingEngine._safe_rate(marge, revenu),
                    provider_fees=sum((item.provider_fees for item in items), Decimal("0")),
                    execution_cost=sum((item.execution_cost for item in items), Decimal("0")),
                )
            )
        return sorted(results, key=lambda item: item.execution_mode)

    @staticmethod
    def _aggregate_segments(rows):
        grouped = defaultdict(list)
        for row in rows:
            grouped[row.segment_client or "standard"].append(row)

        results = []
        for segment_client, items in grouped.items():
            revenu = sum((item.revenu_brut for item in items), Decimal("0"))
            marge = sum((item.marge_nette for item in items), Decimal("0"))
            results.append(
                SegmentReportRow(
                    segment_client=segment_client,
                    conversions_count=len(items),
                    profitable_count=sum(1 for item in items if item.profitable),
                    volume_destination=sum((item.montant_destination for item in items), Decimal("0")),
                    marge_nette=marge,
                    taux_marge=ReportingEngine._safe_rate(marge, revenu),
                )
            )
        return sorted(results, key=lambda item: item.segment_client)

    @staticmethod
    def _safe_rate(numerator: Decimal, denominator: Decimal) -> Decimal:
        if denominator <= 0:
            return Decimal("0")
        return (numerator / denominator) * Decimal("100")

    @staticmethod
    def _frequency_label(count: int) -> str:
        if count >= 8:
            return "elevee"
        if count >= 3:
            return "moyenne"
        return "faible"

    @staticmethod
    def _merchant_score(*, taux_marge: Decimal, incidents_count: int, delai_moyen: Decimal) -> str:
        # Score simple et explicable pour amorcer le pilotage avant l'EPIC de reporting avance.
        if incidents_count == 0 and delai_moyen <= Decimal("10") and taux_marge >= Decimal("0"):
            return "A"
        if incidents_count <= 1 and delai_moyen <= Decimal("20") and taux_marge >= Decimal("0"):
            return "B"
        if incidents_count <= 2 and taux_marge >= Decimal("0"):
            return "C"
        return "D"
