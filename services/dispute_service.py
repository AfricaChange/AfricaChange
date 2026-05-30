from datetime import datetime

from database import db
from models import AdminAction, AuditLog, Conversion, Dispute, Merchant, Paiement, Transaction


class DisputeService:
    @staticmethod
    def open_transaction_dispute(*, tx: Transaction, admin_id: int, ip: str, reason: str, details: str = None, suspend_merchant: bool = False):
        if not admin_id:
            raise PermissionError("Acces administrateur requis")
        if not reason:
            raise ValueError("Motif obligatoire")

        paiement = Paiement.query.filter_by(transaction_reference=tx.reference).first()
        conversion = paiement.conversion if paiement else None
        merchant = conversion.merchant if conversion else None

        existing = Dispute.query.filter_by(transaction_id=tx.id, status="open").first()
        if existing:
            raise ValueError("Un litige ouvert existe deja pour cette transaction")

        dispute = Dispute(
            reference=f"DSP-{tx.reference}",
            transaction_id=tx.id,
            conversion_id=conversion.id if conversion else None,
            merchant_id=merchant.id if merchant else None,
            reason=reason,
            details=details,
            status="open",
            opened_by_admin_id=admin_id,
        )
        db.session.add(dispute)

        db.session.add(
            AdminAction(
                admin_id=admin_id,
                action_type="open_dispute",
                target_type="transaction",
                target_reference=tx.reference,
                reason=reason,
                ip_address=ip,
            )
        )
        db.session.add(
            AuditLog(
                actor_type="admin",
                actor_id=admin_id,
                event="dispute_opened",
                payload={
                    "dispute_reference": dispute.reference,
                    "transaction_reference": tx.reference,
                    "merchant_id": merchant.id if merchant else None,
                },
                ip_address=ip,
            )
        )

        if suspend_merchant and merchant:
            DisputeService.suspend_merchant(
                merchant=merchant,
                admin_id=admin_id,
                ip=ip,
                reason=f"dispute:{dispute.reference}",
            )

        return dispute

    @staticmethod
    def suspend_merchant(*, merchant: Merchant, admin_id: int, ip: str, reason: str):
        if not admin_id:
            raise PermissionError("Acces administrateur requis")
        if merchant.suspended_at and not merchant.actif:
            raise ValueError("Marchand deja suspendu")

        merchant.actif = False
        merchant.suspended_at = datetime.utcnow()
        merchant.suspension_reason = reason

        db.session.add(
            AdminAction(
                admin_id=admin_id,
                action_type="suspend_merchant",
                target_type="merchant",
                target_reference=merchant.code,
                reason=reason,
                ip_address=ip,
            )
        )
        db.session.add(
            AuditLog(
                actor_type="admin",
                actor_id=admin_id,
                event="merchant_suspended",
                payload={"merchant_id": merchant.id, "merchant_code": merchant.code, "reason": reason},
                ip_address=ip,
            )
        )
        return merchant

    @staticmethod
    def reinstate_merchant(*, merchant: Merchant, admin_id: int, ip: str, reason: str = None):
        if not admin_id:
            raise PermissionError("Acces administrateur requis")

        merchant.actif = True
        merchant.suspended_at = None
        merchant.suspension_reason = None

        db.session.add(
            AdminAction(
                admin_id=admin_id,
                action_type="reinstate_merchant",
                target_type="merchant",
                target_reference=merchant.code,
                reason=reason,
                ip_address=ip,
            )
        )
        db.session.add(
            AuditLog(
                actor_type="admin",
                actor_id=admin_id,
                event="merchant_reinstated",
                payload={"merchant_id": merchant.id, "merchant_code": merchant.code},
                ip_address=ip,
            )
        )
        return merchant

    @staticmethod
    def resolve_dispute(*, dispute: Dispute, admin_id: int, ip: str, resolution_note: str = None):
        if not admin_id:
            raise PermissionError("Acces administrateur requis")
        if dispute.status != "open":
            raise ValueError("Seuls les litiges ouverts peuvent etre resolus")

        dispute.status = "resolved"
        dispute.resolved_by_admin_id = admin_id
        dispute.resolved_at = datetime.utcnow()
        if resolution_note:
            dispute.details = f"{dispute.details or ''}\nResolution: {resolution_note}".strip()

        db.session.add(
            AdminAction(
                admin_id=admin_id,
                action_type="resolve_dispute",
                target_type="dispute",
                target_reference=dispute.reference,
                reason=resolution_note,
                ip_address=ip,
            )
        )
        db.session.add(
            AuditLog(
                actor_type="admin",
                actor_id=admin_id,
                event="dispute_resolved",
                payload={"dispute_reference": dispute.reference},
                ip_address=ip,
            )
        )
        return dispute
