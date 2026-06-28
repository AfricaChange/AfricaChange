from datetime import datetime, timedelta

from models import Conversion, Dispute, Merchant, Settlement
from services.wallet_service import WalletService


class MerchantDashboardService:
    @staticmethod
    def snapshot(merchant: Merchant):
        cutoff = datetime.utcnow() - timedelta(days=30)
        balance_breakdown = WalletService.balances_for_merchant(merchant)
        conversions = (
            Conversion.query
            .filter_by(merchant_id=merchant.id)
            .order_by(Conversion.date_conversion.desc())
            .all()
        )

        total_conversions = len(conversions)
        successful_conversions = [c for c in conversions if c.statut == "valide"]
        conversions_30_days = [c for c in conversions if c.date_conversion and c.date_conversion >= cutoff]
        successful_30_days = [c for c in successful_conversions if c.date_conversion and c.date_conversion >= cutoff]

        volume_30_days = round(sum(float(c.montant_converti or 0.0) for c in conversions_30_days), 2)
        success_rate = round((len(successful_conversions) / total_conversions) * 100, 2) if total_conversions else 0.0
        average_processing_minutes = MerchantDashboardService._average_processing_minutes(successful_conversions)
        open_disputes = Dispute.query.filter_by(merchant_id=merchant.id, status="open").count()

        commissions_generated = round(
            sum(float(c.platform_fee or 0.0) for c in successful_conversions),
            2,
        )
        settlements_pending = Settlement.query.filter_by(merchant_id=merchant.id, status="pending").count()
        settlements_completed = Settlement.query.filter_by(merchant_id=merchant.id, status="completed").count()
        currency_breakdown = MerchantDashboardService._currency_breakdown(
            conversions=conversions,
            disputes=(
                Dispute.query
                .filter_by(merchant_id=merchant.id)
                .all()
            ),
            settlements=(
                Settlement.query
                .filter_by(merchant_id=merchant.id)
                .all()
            ),
            cutoff=cutoff,
        )
        solde_disponible = round(
            sum(row["available_balance"] for row in balance_breakdown),
            2,
        ) if balance_breakdown else round(float(merchant.solde_disponible or 0.0), 2)
        solde_verrouille = round(
            sum(row["locked_balance"] for row in balance_breakdown),
            2,
        ) if balance_breakdown else round(float(merchant.solde_verrouille or 0.0), 2)
        solde_pending = round(
            sum(row["pending_balance"] for row in balance_breakdown),
            2,
        ) if balance_breakdown else 0.0

        return {
            "merchant": merchant,
            "solde_disponible": solde_disponible,
            "solde_verrouille": solde_verrouille,
            "solde_pending": solde_pending,
            "volume_30_days": volume_30_days,
            "conversions_count": total_conversions,
            "successful_conversions_30_days": len(successful_30_days),
            "success_rate": success_rate,
            "average_processing_minutes": average_processing_minutes,
            "open_disputes": open_disputes,
            "commissions_generated": commissions_generated,
            "platform_fees_generated": commissions_generated,
            "settlements_pending": settlements_pending,
            "settlements_completed": settlements_completed,
            "balance_breakdown": balance_breakdown,
            "currency_breakdown": currency_breakdown,
            "recent_conversions": conversions[:10],
            "recent_disputes": (
                Dispute.query
                .filter_by(merchant_id=merchant.id)
                .order_by(Dispute.created_at.desc())
                .limit(5)
                .all()
            ),
            "recent_settlements": (
                Settlement.query
                .filter_by(merchant_id=merchant.id)
                .order_by(Settlement.created_at.desc())
                .limit(5)
                .all()
            ),
        }

    @staticmethod
    def _average_processing_minutes(conversions):
        durations = []
        for conversion in conversions:
            end_time = None
            if conversion.settlement and conversion.settlement.settled_at:
                end_time = conversion.settlement.settled_at
            elif conversion.settlement and conversion.settlement.created_at:
                end_time = conversion.settlement.created_at
            elif conversion.paiement and conversion.paiement.date_paiement:
                end_time = conversion.paiement.date_paiement

            if end_time and conversion.date_conversion:
                delta = end_time - conversion.date_conversion
                durations.append(delta.total_seconds() / 60)

        if not durations:
            return 0.0

        return round(sum(durations) / len(durations), 2)

    @staticmethod
    def _currency_breakdown(*, conversions, disputes, settlements, cutoff):
        grouped = {}

        for conversion in conversions:
            currency = conversion.to_currency or "N/A"
            row = grouped.setdefault(
                currency,
                {
                    "currency": currency,
                    "volume_30_days": 0.0,
                    "conversions_count": 0,
                    "successful_count": 0,
                    "success_rate": 0.0,
                    "average_processing_minutes": 0.0,
                    "open_disputes": 0,
                    "commissions_generated": 0.0,
                    "platform_fees_generated": 0.0,
                    "settlements_pending": 0,
                    "settlements_completed": 0,
                },
            )
            row["conversions_count"] += 1
            if conversion.date_conversion and conversion.date_conversion >= cutoff:
                row["volume_30_days"] += float(conversion.montant_converti or 0.0)
            if conversion.statut == "valide":
                row["successful_count"] += 1
                row["commissions_generated"] += float(conversion.platform_fee or 0.0)
                row["platform_fees_generated"] += float(conversion.platform_fee or 0.0)

        for dispute in disputes:
            currency = dispute.conversion.to_currency if dispute.conversion and dispute.conversion.to_currency else "N/A"
            row = grouped.setdefault(
                currency,
                {
                    "currency": currency,
                    "volume_30_days": 0.0,
                    "conversions_count": 0,
                    "successful_count": 0,
                    "success_rate": 0.0,
                    "average_processing_minutes": 0.0,
                    "open_disputes": 0,
                    "commissions_generated": 0.0,
                    "platform_fees_generated": 0.0,
                    "settlements_pending": 0,
                    "settlements_completed": 0,
                },
            )
            if dispute.status == "open":
                row["open_disputes"] += 1

        for settlement in settlements:
            currency = settlement.currency or "N/A"
            row = grouped.setdefault(
                currency,
                {
                    "currency": currency,
                    "volume_30_days": 0.0,
                    "conversions_count": 0,
                    "successful_count": 0,
                    "success_rate": 0.0,
                    "average_processing_minutes": 0.0,
                    "open_disputes": 0,
                    "commissions_generated": 0.0,
                    "platform_fees_generated": 0.0,
                    "settlements_pending": 0,
                    "settlements_completed": 0,
                },
            )
            if settlement.status == "pending":
                row["settlements_pending"] += 1
            elif settlement.status == "completed":
                row["settlements_completed"] += 1

        for currency, row in grouped.items():
            row["volume_30_days"] = round(row["volume_30_days"], 2)
            row["commissions_generated"] = round(row["commissions_generated"], 2)
            row["platform_fees_generated"] = round(row["platform_fees_generated"], 2)
            row["success_rate"] = round(
                (row["successful_count"] / row["conversions_count"]) * 100,
                2,
            ) if row["conversions_count"] else 0.0

            currency_conversions = [c for c in conversions if (c.to_currency or "N/A") == currency and c.statut == "valide"]
            row["average_processing_minutes"] = MerchantDashboardService._average_processing_minutes(currency_conversions)

        return sorted(grouped.values(), key=lambda item: item["currency"])
