from datetime import datetime, timedelta

from database import db
from models import CompteSysteme, Conversion, MerchantRate, Paiement, Parametre, Settlement
from services.constants import PaymentStatus
from services.ledger_service import LedgerService
from services.wallet_service import WalletService


class LiquidityService:
    PLATFORM = "platform"
    MERCHANT = "merchant"
    MAX_MERCHANT_RISK_SCORE = 70
    DEFAULT_RESERVATION_MINUTES = 15

    @staticmethod
    def assign_for_conversion(conversion: Conversion):
        if conversion.liquidity_source_type == LiquidityService.MERCHANT and conversion.merchant_id:
            return conversion
        if conversion.liquidity_source_type == LiquidityService.PLATFORM and conversion.compte_systeme_id:
            return conversion

        merchant_rate = LiquidityService._find_merchant_rate(conversion)
        if merchant_rate:
            LiquidityService._reserve_merchant_liquidity(conversion, merchant_rate)
            return conversion

        LiquidityService._assign_platform_liquidity(conversion)
        return conversion

    @staticmethod
    def finalize_from_transaction_reference(transaction_reference: str, success: bool, failure_status=None):
        paiement = Paiement.query.filter_by(transaction_reference=transaction_reference).first()
        if not paiement or not paiement.conversion:
            return

        LiquidityService.finalize_conversion(
            paiement.conversion,
            success=success,
            failure_status=failure_status,
        )

    @staticmethod
    def finalize_conversion(conversion: Conversion, success: bool, failure_status=None):
        if not conversion:
            return

        if success:
            conversion.statut = PaymentStatus.VALIDE.value
            if conversion.liquidity_source_type == LiquidityService.MERCHANT and conversion.merchant:
                gross_amount = float(conversion.locked_amount or 0.0)
                platform_fee = min(float(conversion.platform_fee or 0.0), gross_amount)
                net_amount = round(gross_amount - platform_fee, 2)
                WalletService.lock_to_pending(
                    merchant=conversion.merchant,
                    currency=conversion.to_currency,
                    gross_amount=gross_amount,
                    net_amount=net_amount,
                    reference=conversion.reference,
                    description="Liquidite verrouillee basculee en reglement pending",
                    context={
                        "provider": "merchant",
                        "merchant_id": conversion.merchant_id,
                        "conversion_id": conversion.id,
                        "conversion_reference": conversion.reference,
                        "platform_fee": platform_fee,
                    },
                )
                LiquidityService._ensure_pending_settlement(conversion)
                conversion.settlement_status = "ready_for_settlement"
                conversion.reserved_until = None
            else:
                conversion.settlement_status = "completed"
            return

        conversion.statut = failure_status or PaymentStatus.ECHOUE.value
        if conversion.liquidity_source_type == LiquidityService.MERCHANT and conversion.merchant:
            LiquidityService.release_expired_reservation(
                conversion,
                reason=failure_status or "payment_failure",
                auto_commit=False,
            )

    @staticmethod
    def _find_merchant_rate(conversion: Conversion):
        query = (
            MerchantRate.query
            .join(MerchantRate.merchant)
            .filter(
                MerchantRate.actif.is_(True),
                MerchantRate.from_currency == conversion.from_currency,
                MerchantRate.to_currency == conversion.to_currency,
                MerchantRate.rate >= LiquidityService._quoted_rate(conversion),
            )
        )

        candidates = query.all()
        eligible = []
        for merchant_rate in candidates:
            merchant = merchant_rate.merchant
            if merchant.pays != LiquidityService._map_currency_to_country(conversion.to_currency):
                continue
            if merchant.risk_score > LiquidityService.MAX_MERCHANT_RISK_SCORE:
                continue
            if not merchant.can_handle_currency(conversion.to_currency, conversion.montant_converti):
                continue
            eligible.append(merchant_rate)

        eligible.sort(key=lambda item: (item.merchant.risk_score, -item.rate, item.merchant.id))
        return eligible[0] if eligible else None

    @staticmethod
    def _reserve_merchant_liquidity(conversion: Conversion, merchant_rate: MerchantRate):
        merchant = merchant_rate.merchant
        amount = float(conversion.montant_converti)

        WalletService.lock(
            merchant=merchant,
            currency=conversion.to_currency,
            amount=amount,
            reference=conversion.reference,
            description="Reservation liquidite marchand",
            context={
                "provider": "merchant",
                "merchant_id": merchant.id,
                "conversion_id": conversion.id,
                "conversion_reference": conversion.reference,
            },
        )

        LedgerService.record(
            reference=conversion.reference,
            compte=f"merchant_{merchant.id}_available",
            sens="debit",
            montant=amount,
            devise=conversion.to_currency,
            provider="merchant",
            conversion_id=conversion.id,
            description="Reservation liquidite marchand",
        )
        LedgerService.record(
            reference=conversion.reference,
            compte=f"merchant_{merchant.id}_locked",
            sens="credit",
            montant=amount,
            devise=conversion.to_currency,
            provider="merchant",
            conversion_id=conversion.id,
            description="Liquidite marchand verrouillee",
        )

        conversion.liquidity_source_type = LiquidityService.MERCHANT
        conversion.risk_bearer = LiquidityService.MERCHANT
        conversion.merchant_id = merchant.id
        conversion.merchant_rate_id = merchant_rate.id
        conversion.assigned_rate = merchant_rate.rate
        conversion.locked_amount = amount
        conversion.platform_fee = LiquidityService._platform_fee(conversion)
        conversion.settlement_status = "reserved"
        conversion.reserved_until = LiquidityService._reservation_deadline()
        conversion.selection_reason = "eligible_verified_merchant"

    @staticmethod
    def _assign_platform_liquidity(conversion: Conversion):
        pays_cible = LiquidityService._map_currency_to_country(conversion.to_currency)
        compte_systeme = (
            CompteSysteme.query
            .filter_by(pays=pays_cible, actif=True)
            .order_by(CompteSysteme.id.asc())
            .first()
        )

        if not compte_systeme:
            raise ValueError("Aucune liquidite disponible pour cette devise")

        conversion.compte_systeme_id = compte_systeme.id
        conversion.liquidity_source_type = LiquidityService.PLATFORM
        conversion.risk_bearer = LiquidityService.PLATFORM
        conversion.assigned_rate = LiquidityService._quoted_rate(conversion)
        conversion.platform_fee = LiquidityService._platform_fee(conversion)
        conversion.locked_amount = 0.0
        conversion.settlement_status = "pending"
        conversion.reserved_until = None
        conversion.selection_reason = "platform_fallback"

    @staticmethod
    def _platform_fee(conversion: Conversion) -> float:
        param = Parametre.query.filter_by(cle="platform_fee_rate").first()
        try:
            fee_rate = float(param.valeur) if param and param.valeur is not None else 0.0
        except (TypeError, ValueError):
            fee_rate = 0.0
        return round(float(conversion.montant_converti) * fee_rate / 100, 2)

    @staticmethod
    def _quoted_rate(conversion: Conversion) -> float:
        if conversion.montant_initial <= 0:
            return 0.0
        return round(float(conversion.montant_converti) / float(conversion.montant_initial), 8)

    @staticmethod
    def _map_currency_to_country(currency: str):
        return {
            "CFA": "SN",
            "GNF": "GN",
        }.get(currency)

    @staticmethod
    def release_expired_reservation(conversion: Conversion, reason: str = "reservation_expired", auto_commit: bool = False):
        if not conversion or conversion.liquidity_source_type != LiquidityService.MERCHANT or not conversion.merchant:
            return False

        amount = float(conversion.locked_amount or 0.0)
        if amount <= 0:
            return False

        merchant = conversion.merchant
        WalletService.unlock(
            merchant=merchant,
            currency=conversion.to_currency,
            amount=amount,
            reference=conversion.reference,
            description=f"Release liquidite marchand: {reason}",
            context={
                "provider": "merchant",
                "merchant_id": merchant.id,
                "conversion_id": conversion.id,
                "conversion_reference": conversion.reference,
                "release_reason": reason,
            },
        )

        LedgerService.record(
            reference=conversion.reference,
            compte=f"merchant_{merchant.id}_locked",
            sens="debit",
            montant=amount,
            devise=conversion.to_currency,
            provider="merchant",
            conversion_id=conversion.id,
            description=f"Release liquidite marchand: {reason}",
        )
        LedgerService.record(
            reference=conversion.reference,
            compte=f"merchant_{merchant.id}_available",
            sens="credit",
            montant=amount,
            devise=conversion.to_currency,
            provider="merchant",
            conversion_id=conversion.id,
            description=f"Retour liquidite disponible: {reason}",
        )

        conversion.statut = PaymentStatus.ECHOUE.value
        conversion.settlement_status = "released"
        conversion.locked_amount = 0.0
        conversion.reserved_until = None
        conversion.selection_reason = reason
        return True

    @staticmethod
    def expire_stale_reservations(now=None):
        now = now or datetime.utcnow()
        conversions = (
            Conversion.query
            .filter(
                Conversion.liquidity_source_type == LiquidityService.MERCHANT,
                Conversion.statut == PaymentStatus.EN_COURS.value,
                Conversion.reserved_until.isnot(None),
                Conversion.reserved_until < now,
            )
            .all()
        )

        expired_references = []
        for conversion in conversions:
            if LiquidityService.release_expired_reservation(conversion, reason="reservation_expired"):
                expired_references.append(conversion.reference)

        return expired_references

    @staticmethod
    def _reservation_deadline():
        param = Parametre.query.filter_by(cle="merchant_reservation_timeout_minutes").first()
        try:
            minutes = int(param.valeur) if param and param.valeur is not None else LiquidityService.DEFAULT_RESERVATION_MINUTES
        except (TypeError, ValueError):
            minutes = LiquidityService.DEFAULT_RESERVATION_MINUTES
        minutes = max(1, minutes)
        return datetime.utcnow() + timedelta(minutes=minutes)

    @staticmethod
    def _ensure_pending_settlement(conversion: Conversion):
        existing = Settlement.query.filter_by(conversion_id=conversion.id).first()
        if existing:
            return existing

        gross_amount = float(conversion.locked_amount or conversion.montant_converti or 0.0)
        platform_fee = min(float(conversion.platform_fee or 0.0), gross_amount)
        net_amount = round(gross_amount - platform_fee, 2)

        settlement = Settlement(
            reference=f"STL-{conversion.reference}",
            conversion_id=conversion.id,
            merchant_id=conversion.merchant_id,
            gross_amount=gross_amount,
            platform_fee=platform_fee,
            net_amount=net_amount,
            currency=conversion.to_currency,
            status="pending",
        )
        db.session.add(settlement)

        LedgerService.record(
            reference=settlement.reference,
            compte=f"merchant_{conversion.merchant_id}_locked",
            sens="debit",
            montant=gross_amount,
            devise=conversion.to_currency,
            provider="merchant",
            conversion_id=conversion.id,
            description="Deblocage liquidite pour reglement marchand",
        )
        LedgerService.record(
            reference=settlement.reference,
            compte="merchant_settlement_pending",
            sens="credit",
            montant=net_amount,
            devise=conversion.to_currency,
            provider="merchant",
            conversion_id=conversion.id,
            description="Dette envers marchand a regler",
        )
        if platform_fee > 0:
            LedgerService.record(
                reference=settlement.reference,
                compte="platform_fee_revenue_pending",
                sens="credit",
                montant=platform_fee,
                devise=conversion.to_currency,
                provider="platform",
                conversion_id=conversion.id,
                description="Commission plateforme sur reglement marchand",
            )

        return settlement
