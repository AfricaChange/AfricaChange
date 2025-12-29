from database import db
from models import Transaction, AdminAction, AuditLog, Refund
from services.ledger_service import LedgerService
from services.risk_engine import RiskEngine
from services.constants import PaymentStatus
from datetime import datetime


class AdminActions:
    """
    Actions critiques ADMIN :
    - validate
    - block
    - refund
    Toutes les actions sont tracées et auditées
    """

    # --------------------------------------------------
    # 🔐 CHECK ADMIN
    # --------------------------------------------------
    @staticmethod
    def _require_admin(admin_id):
        if not admin_id:
            raise PermissionError("Accès administrateur requis")

    @staticmethod
    def _log_action(admin_id, action, target, reference, reason, ip):
        db.session.add(AdminAction(
            admin_id=admin_id,
            action_type=action,
            target_type=target,
            target_reference=reference,
            reason=reason,
            ip_address=ip
        ))

    @staticmethod
    def _audit(event, payload, ip):
        db.session.add(AuditLog(
            actor_type="admin",
            event=event,
            payload=payload,
            ip_address=ip
        ))

    # ==================================================
    # ✅ VALIDATION MANUELLE
    # ==================================================
    @staticmethod
    def validate(*, tx: Transaction, admin_id, ip, reason=None):
        AdminActions._require_admin(admin_id)

        if tx.statut == PaymentStatus.VALIDE.value:
            raise ValueError("Transaction déjà validée")

        tx.statut = PaymentStatus.VALIDE.value

        LedgerService.record(
            reference=tx.reference,
            compte="system_manual",
            sens="credit",
            montant=tx.montant,
            devise="XOF",
            provider="admin",
            transaction_id=tx.id,
            description="Validation manuelle admin"
        )

        AdminActions._log_action(
            admin_id, "validate", "transaction",
            tx.reference, reason, ip
        )

        AdminActions._audit(
            "transaction_validated",
            {"reference": tx.reference},
            ip
        )

    # ==================================================
    # ⛔ BLOQUER TRANSACTION
    # ==================================================
    @staticmethod
    def block(*, tx: Transaction, admin_id, ip, reason):
        AdminActions._require_admin(admin_id)

        if tx.statut in (
            PaymentStatus.BLOQUE.value,
            PaymentStatus.REMBOURSE.value
        ):
            raise ValueError("Transaction déjà traitée")

        tx.statut = PaymentStatus.BLOQUE.value

        RiskEngine.log(
            reference=tx.reference,
            provider=tx.fournisseur,
            ip=ip,
            risk_type="admin_block",
            score=100,
            details=reason
        )

        AdminActions._log_action(
            admin_id, "block", "transaction",
            tx.reference, reason, ip
        )

        AdminActions._audit(
            "transaction_blocked",
            {"reference": tx.reference},
            ip
        )

    # ==================================================
    # 💸 REMBOURSEMENT
    # ==================================================
    @staticmethod
    def refund(*, tx: Transaction, admin_id, ip, amount, reason):
        AdminActions._require_admin(admin_id)

        if tx.statut != PaymentStatus.VALIDE.value:
            raise ValueError("Seules les transactions validées sont remboursables")

        refund = Refund(
            transaction_id=tx.id,
            amount=amount,
            reason=reason,
            admin_id=admin_id,
            status="completed"  # statut interne refund
        )
        db.session.add(refund)

        LedgerService.record(
            reference=f"REFUND-{tx.reference}",
            compte="system_refund",
            sens="debit",
            montant=amount,
            devise="XOF",
            provider="admin",
            transaction_id=tx.id,
            description="Remboursement admin"
        )

        tx.statut = PaymentStatus.REMBOURSE.value

        AdminActions._log_action(
            admin_id, "refund", "transaction",
            tx.reference, reason, ip
        )

        AdminActions._audit(
            "refund_processed",
            {"reference": tx.reference, "amount": amount},
            ip
        )
