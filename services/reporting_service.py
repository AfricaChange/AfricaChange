from datetime import datetime
from decimal import Decimal

from engines.profitability_engine import ProfitabilityEngine, ProfitabilityInput
from engines.reporting_engine import ReportingEngine, ReportingInputRow
from models import Conversion


class ReportingService:
    INCIDENT_STATUSES = {
        "execution_failed",
        "manual_review_required",
        "cancelled",
        "expired",
        "rejected",
        "payout_pending_verification",
    }
    DEFINITIVE_STATUSES = {
        "completed",
        "cancelled",
        "expired",
        "rejected",
    }

    @staticmethod
    def build_rows(*, conversions=None):
        dataset = conversions
        if dataset is None:
            dataset = Conversion.query.order_by(Conversion.date_conversion.desc()).all()

        return [ReportingService._build_row(conversion) for conversion in dataset]

    @staticmethod
    def generate_snapshot(*, conversions=None):
        return ReportingEngine.generer(ReportingService.build_rows(conversions=conversions))

    @staticmethod
    def filter_rows(
        rows,
        *,
        start_date=None,
        end_date=None,
        corridor="",
        currency="",
        merchant_id=None,
        execution_mode="",
        statut="",
    ):
        filtered = list(rows)

        if start_date is not None:
            filtered = [row for row in filtered if row.created_at and row.created_at.date() >= start_date]
        if end_date is not None:
            filtered = [row for row in filtered if row.created_at and row.created_at.date() <= end_date]
        if corridor:
            filtered = [row for row in filtered if row.corridor == corridor]
        if currency:
            filtered = [row for row in filtered if row.devise_source == currency or row.devise_cible == currency]
        if merchant_id is not None:
            filtered = [row for row in filtered if row.merchant_id == merchant_id]
        if execution_mode:
            filtered = [row for row in filtered if row.execution_mode == execution_mode]
        if statut:
            filtered = [row for row in filtered if row.statut == statut]
        return filtered

    @staticmethod
    def generate_dashboard(
        *,
        conversions=None,
        start_date=None,
        end_date=None,
        corridor="",
        currency="",
        merchant_id=None,
        execution_mode="",
        statut="",
        detail_limit=25,
    ):
        rows = ReportingService.build_rows(conversions=conversions)
        filtered_rows = ReportingService.filter_rows(
            rows,
            start_date=start_date,
            end_date=end_date,
            corridor=corridor,
            currency=currency,
            merchant_id=merchant_id,
            execution_mode=execution_mode,
            statut=statut,
        )
        snapshot = ReportingEngine.generer(filtered_rows)
        sorted_rows = sorted(filtered_rows, key=lambda row: row.created_at or datetime.min, reverse=True)
        losses = [row for row in sorted_rows if row.marge_nette < 0]
        below_forecast = [row for row in sorted_rows if row.sous_prevision]
        provisional = [row for row in sorted_rows if row.provisoire]
        definitive = [row for row in sorted_rows if not row.provisoire]

        return {
            "snapshot": snapshot,
            "rows": sorted_rows[:detail_limit],
            "transactions_en_perte": losses[:detail_limit],
            "transactions_sous_prevision": below_forecast[:detail_limit],
            "conversions_provisoires": provisional[:detail_limit],
            "totaux": {
                "conversions_count": len(filtered_rows),
                "marge_nette": sum((row.marge_nette for row in filtered_rows), Decimal("0")),
                "revenu_brut": sum((row.revenu_brut for row in filtered_rows), Decimal("0")),
                "pertes_count": len(losses),
                "sous_prevision_count": len(below_forecast),
                "provisoires_count": len(provisional),
                "definitives_count": len(definitive),
            },
        }

    @staticmethod
    def _build_row(conversion):
        execution = conversion.execution
        profitability = ReportingService._profitability(conversion, execution)
        offer_snapshot = conversion.offer_snapshot or {}
        corridor = offer_snapshot.get("corridor") or f"{conversion.from_currency}->{conversion.to_currency}"
        segment_client = offer_snapshot.get("segment_client") or "standard"
        classification_flux = offer_snapshot.get("classification_flux") or "ponctuel"
        client_reference = f"USR-{conversion.user.id}" if conversion.user else f"CONV-{conversion.reference}"
        client_nom = (
            f"{conversion.user.prenom} {conversion.user.nom}".strip()
            if conversion.user
            else "Client inconnu"
        )
        execution_status = execution.status if execution else (conversion.statut or "")
        execution_mode = (
            conversion.execution_mode
            or conversion.liquidity_source_type
            or (execution.mode if execution else None)
            or "inconnu"
        )
        execution_cost = Decimal(str(execution.execution_cost or 0)) if execution else Decimal("0")
        provider_fees = Decimal(str(execution.provider_fees or 0)) if execution else Decimal("0")
        delay_minutes = ReportingService._delay_minutes(execution)
        marge_estimee = Decimal(str(conversion.margin_estimated or conversion.platform_fee or 0))
        provisoire = execution_status not in ReportingService.DEFINITIVE_STATUSES
        sous_prevision = profitability.marge_nette_reelle < marge_estimee

        return ReportingInputRow(
            conversion_reference=conversion.reference or "",
            corridor=corridor,
            merchant_id=conversion.merchant_id or 0,
            merchant_code=conversion.merchant.code if conversion.merchant else "",
            merchant_nom=conversion.merchant.nom if conversion.merchant else "",
            client_reference=client_reference,
            client_nom=client_nom,
            segment_client=segment_client,
            classification_flux=classification_flux,
            devise_source=conversion.from_currency or "",
            devise_cible=conversion.to_currency or "",
            execution_mode=execution_mode,
            liquidity_source_type=conversion.liquidity_source_type or "",
            provider_code=(execution.provider_code if execution else "") or "",
            statut=execution_status,
            montant_source=ReportingService._source_amount(conversion),
            montant_destination=ReportingService._target_amount(conversion),
            revenu_brut=profitability.revenu_brut,
            marge_estimee=marge_estimee,
            marge_nette=profitability.marge_nette_reelle,
            ecart_prevision_reel=profitability.ecart_prevision_reel,
            execution_cost=execution_cost,
            provider_fees=provider_fees,
            delai_execution_minutes=delay_minutes,
            profitable=profitability.profitable,
            incident=execution_status in ReportingService.INCIDENT_STATUSES,
            provisoire=provisoire,
            sous_prevision=sous_prevision,
            created_at=conversion.date_conversion,
        )

    @staticmethod
    def _profitability(conversion, execution):
        margin_estimated = Decimal(str(conversion.margin_estimated or conversion.platform_fee or 0))
        destination_amount = ReportingService._target_amount(conversion)
        execution_cost = Decimal(str(execution.execution_cost or 0)) if execution else Decimal("0")

        profitability_input = ProfitabilityInput(
            conversion_reference=conversion.reference or "",
            devise_reference=conversion.to_currency or "",
            montant_source_client=ReportingService._source_amount(conversion),
            montant_destination_client=destination_amount,
            taux_client=Decimal(str(conversion.client_rate or conversion.assigned_rate or 0)),
            marge_estimee=margin_estimated,
            cout_liquidite_estime=destination_amount,
            cout_liquidite_reel=destination_amount,
            frais_payin_reels=Decimal("0"),
            frais_payout_reels=execution_cost,
            frais_marchand_reels=Decimal("0"),
            autres_couts_reels=Decimal("0"),
            commissions_client=Decimal("0"),
            commissions_marchand=Decimal("0"),
            mode_execution=(execution.mode if execution else conversion.execution_mode) or "",
            provider_code=(execution.provider_code if execution else "") or "",
            corridor=(conversion.offer_snapshot or {}).get("corridor") or f"{conversion.from_currency}->{conversion.to_currency}",
            segment_client=(conversion.offer_snapshot or {}).get("segment_client") or "standard",
            classification_flux=(conversion.offer_snapshot or {}).get("classification_flux") or "ponctuel",
            provisoire=bool(execution and execution.completed_at is None and execution.status not in {"completed", "cancelled", "expired"}),
            annulee=conversion.statut == "cancelled",
            remboursee=False,
        )
        return ProfitabilityEngine.analyse(profitability_input)

    @staticmethod
    def _source_amount(conversion):
        return Decimal(str(conversion.quote_source_amount or conversion.montant_initial or 0))

    @staticmethod
    def _target_amount(conversion):
        return Decimal(str(conversion.quote_target_amount or conversion.montant_converti or 0))

    @staticmethod
    def _delay_minutes(execution):
        if execution is None or execution.started_at is None or execution.completed_at is None:
            return Decimal("0")
        delta = execution.completed_at - execution.started_at
        return Decimal(str(delta.total_seconds() / 60))
