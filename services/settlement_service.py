from datetime import datetime

from database import db
from models import AuditLog, Settlement
from services.ledger_service import LedgerService


class SettlementService:
    @staticmethod
    def complete_settlement(*, settlement: Settlement, admin_id: int, ip: str, notes: str = None):
        if not admin_id:
            raise PermissionError("Acces administrateur requis")
        if settlement.status != "pending":
            raise ValueError("Seuls les reglements en attente peuvent etre clotures")

        settlement.status = "completed"
        settlement.approved_by_admin_id = admin_id
        settlement.notes = notes
        settlement.settled_at = datetime.utcnow()

        if settlement.conversion:
            settlement.conversion.settlement_status = "completed"

        LedgerService.record(
            reference=settlement.reference,
            compte="merchant_settlement_pending",
            sens="debit",
            montant=settlement.net_amount,
            devise=settlement.currency,
            provider="merchant",
            conversion_id=settlement.conversion_id,
            description="Extinction de dette marchand",
        )
        LedgerService.record(
            reference=settlement.reference,
            compte=f"merchant_{settlement.merchant_id}_settled",
            sens="credit",
            montant=settlement.net_amount,
            devise=settlement.currency,
            provider="merchant",
            conversion_id=settlement.conversion_id,
            description="Reglement marchand execute",
        )

        if settlement.platform_fee > 0:
            LedgerService.record(
                reference=settlement.reference,
                compte="platform_fee_revenue_pending",
                sens="debit",
                montant=settlement.platform_fee,
                devise=settlement.currency,
                provider="platform",
                conversion_id=settlement.conversion_id,
                description="Sortie du revenu plateforme en attente",
            )
            LedgerService.record(
                reference=settlement.reference,
                compte="platform_fee_revenue_realized",
                sens="credit",
                montant=settlement.platform_fee,
                devise=settlement.currency,
                provider="platform",
                conversion_id=settlement.conversion_id,
                description="Commission plateforme realisee",
            )

        db.session.add(
            AuditLog(
                actor_type="admin",
                actor_id=admin_id,
                event="merchant_settlement_completed",
                payload={
                    "settlement_reference": settlement.reference,
                    "conversion_reference": settlement.conversion.reference if settlement.conversion else None,
                    "merchant_id": settlement.merchant_id,
                    "net_amount": settlement.net_amount,
                    "currency": settlement.currency,
                },
                ip_address=ip,
            )
        )

        return settlement
