from datetime import datetime
from decimal import Decimal

from database import db
from models import AdminWalletAction, AuditLog, Currency, Merchant, Parametre
from services.wallet_service import WalletService


class MerchantWalletAdminService:
    ACTIONS = {
        "credit": WalletService.credit,
        "debit": WalletService.debit,
        "lock": WalletService.lock,
        "unlock": WalletService.unlock,
    }

    @staticmethod
    def execute(
        *,
        merchant: Merchant,
        action: str,
        currency: str,
        amount,
        admin_user_id: int,
        ip_address: str,
        reason: str,
        reference: str = None,
        session_identifier: str = None,
        high_amount_confirmed: bool = False,
    ):
        if action not in MerchantWalletAdminService.ACTIONS:
            raise ValueError("Operation wallet admin invalide.")
        if not admin_user_id:
            raise PermissionError("Acces administrateur requis.")
        if not reason or not str(reason).strip():
            raise ValueError("Le motif est obligatoire.")
        normalized_amount = Decimal(str(amount or 0))
        if normalized_amount <= Decimal("0"):
            raise ValueError("Le montant doit etre strictement positif.")

        currency_row = Currency.query.filter_by(code=str(currency).upper(), is_active=True).first()
        if not currency_row:
            raise ValueError("Devise inconnue ou inactive.")

        MerchantWalletAdminService._assert_high_amount_confirmation(
            amount=normalized_amount,
            confirmed=high_amount_confirmed,
        )

        normalized_reason = str(reason).strip()
        normalized_reference = reference or MerchantWalletAdminService._build_reference(
            merchant_id=merchant.id,
            action=action,
        )
        context = {
            "provider": "admin_wallet",
            "admin_user_id": admin_user_id,
            "merchant_id": merchant.id,
            "reason": normalized_reason,
            "source": "admin_wallet_console",
        }

        MerchantWalletAdminService.ACTIONS[action](
            merchant=merchant,
            currency=currency_row.code,
            amount=normalized_amount,
            reference=normalized_reference,
            description=normalized_reason,
            context=context,
        )

        db.session.add(
            AdminWalletAction(
                requested_by_admin_id=admin_user_id,
                approved_by_admin_id=admin_user_id,
                merchant_id=merchant.id,
                currency_code=currency_row.code,
                action=action,
                amount=normalized_amount,
                reference=normalized_reference,
                reason=normalized_reason,
                ip_address=ip_address,
                session_identifier=session_identifier,
                status="completed",
            )
        )

        db.session.add(
            AuditLog(
                actor_type="admin",
                actor_id=admin_user_id,
                event=f"merchant_wallet_{action}",
                payload={
                    "merchant_id": merchant.id,
                    "merchant_code": merchant.code,
                    "currency": currency_row.code,
                    "amount": str(normalized_amount),
                    "reason": normalized_reason,
                    "reference": normalized_reference,
                },
                ip_address=ip_address,
            )
        )
        db.session.flush()

        return {
            "reference": normalized_reference,
            "balances": WalletService.balances_for_merchant(merchant),
        }

    @staticmethod
    def _build_reference(*, merchant_id: int, action: str) -> str:
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        return f"ADMIN-{action.upper()}-{merchant_id}-{timestamp}"

    @staticmethod
    def _assert_high_amount_confirmation(*, amount: Decimal, confirmed: bool):
        param = Parametre.query.filter_by(cle="admin_wallet_high_amount_threshold").first()
        try:
            threshold = Decimal(str(param.valeur)) if param and param.valeur is not None else Decimal("1000000")
        except Exception:
            threshold = Decimal("1000000")

        if threshold > Decimal("0") and amount >= threshold and not confirmed:
            raise ValueError("Confirmation explicite requise pour ce montant sensible.")
