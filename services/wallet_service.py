from decimal import Decimal

from database import db
from models import Currency, Merchant, MerchantBalance, WalletEntry


class WalletTransactionManager:
    @staticmethod
    def execute(callback):
        result = callback()
        db.session.flush()
        return result


class WalletService:
    ZERO = Decimal("0")

    @staticmethod
    def credit(*, merchant: Merchant, currency: str, amount, reference: str, description: str = None, context=None):
        amount = WalletService._decimal(amount)
        if amount <= WalletService.ZERO:
            raise ValueError("Le montant de credit doit etre strictement positif")

        def operation():
            balance = WalletService._get_or_create_balance(merchant=merchant, currency=currency)
            WalletService._write_entry(
                balance=balance,
                reference=reference,
                operation="credit",
                balance_type="available",
                direction="credit",
                amount=amount,
                description=description,
                context=context,
            )
            WalletService._sync_legacy_fields(merchant)
            return balance

        return WalletTransactionManager.execute(operation)

    @staticmethod
    def debit(*, merchant: Merchant, currency: str, amount, reference: str, description: str = None, context=None):
        amount = WalletService._decimal(amount)
        if amount <= WalletService.ZERO:
            raise ValueError("Le montant de debit doit etre strictement positif")

        def operation():
            balance = WalletService._get_or_create_balance(merchant=merchant, currency=currency)
            WalletService._assert_sufficient(balance.available_balance, amount, "solde disponible insuffisant")
            WalletService._write_entry(
                balance=balance,
                reference=reference,
                operation="debit",
                balance_type="available",
                direction="debit",
                amount=amount,
                description=description,
                context=context,
            )
            WalletService._sync_legacy_fields(merchant)
            return balance

        return WalletTransactionManager.execute(operation)

    @staticmethod
    def lock(*, merchant: Merchant, currency: str, amount, reference: str, description: str = None, context=None):
        amount = WalletService._decimal(amount)
        if amount <= WalletService.ZERO:
            raise ValueError("Le montant a verrouiller doit etre strictement positif")

        def operation():
            balance = WalletService._get_or_create_balance(merchant=merchant, currency=currency)
            WalletService._assert_sufficient(balance.available_balance, amount, "solde disponible insuffisant")
            WalletService._write_entry(
                balance=balance,
                reference=reference,
                operation="lock",
                balance_type="available",
                direction="debit",
                amount=amount,
                description=description or "Verrouillage de liquidite",
                context=context,
            )
            WalletService._write_entry(
                balance=balance,
                reference=reference,
                operation="lock",
                balance_type="locked",
                direction="credit",
                amount=amount,
                description=description or "Verrouillage de liquidite",
                context=context,
            )
            WalletService._sync_legacy_fields(merchant)
            return balance

        return WalletTransactionManager.execute(operation)

    @staticmethod
    def unlock(*, merchant: Merchant, currency: str, amount, reference: str, description: str = None, context=None):
        amount = WalletService._decimal(amount)
        if amount <= WalletService.ZERO:
            raise ValueError("Le montant a deverrouiller doit etre strictement positif")

        def operation():
            balance = WalletService._get_or_create_balance(merchant=merchant, currency=currency)
            WalletService._assert_sufficient(balance.locked_balance, amount, "solde verrouille insuffisant")
            WalletService._write_entry(
                balance=balance,
                reference=reference,
                operation="unlock",
                balance_type="locked",
                direction="debit",
                amount=amount,
                description=description or "Deverrouillage de liquidite",
                context=context,
            )
            WalletService._write_entry(
                balance=balance,
                reference=reference,
                operation="unlock",
                balance_type="available",
                direction="credit",
                amount=amount,
                description=description or "Retour au solde disponible",
                context=context,
            )
            WalletService._sync_legacy_fields(merchant)
            return balance

        return WalletTransactionManager.execute(operation)

    @staticmethod
    def lock_to_pending(
        *,
        merchant: Merchant,
        currency: str,
        gross_amount,
        net_amount,
        reference: str,
        description: str = None,
        context=None,
    ):
        gross_amount = WalletService._decimal(gross_amount)
        net_amount = WalletService._decimal(net_amount)
        if gross_amount <= WalletService.ZERO or net_amount < WalletService.ZERO:
            raise ValueError("Les montants de settlement sont invalides")
        if net_amount > gross_amount:
            raise ValueError("Le montant net ne peut pas depasser le montant brut")

        def operation():
            balance = WalletService._get_or_create_balance(merchant=merchant, currency=currency)
            WalletService._assert_sufficient(balance.locked_balance, gross_amount, "solde verrouille insuffisant")
            WalletService._write_entry(
                balance=balance,
                reference=reference,
                operation="settlement_pending",
                balance_type="locked",
                direction="debit",
                amount=gross_amount,
                description=description or "Transfert vers solde pending",
                context=context,
            )
            if net_amount > WalletService.ZERO:
                WalletService._write_entry(
                    balance=balance,
                    reference=reference,
                    operation="settlement_pending",
                    balance_type="pending",
                    direction="credit",
                    amount=net_amount,
                    description=description or "Reglement marchand en attente",
                    context=context,
                )
            WalletService._sync_legacy_fields(merchant)
            return balance

        return WalletTransactionManager.execute(operation)

    @staticmethod
    def clear_pending(*, merchant: Merchant, currency: str, amount, reference: str, description: str = None, context=None):
        amount = WalletService._decimal(amount)
        if amount <= WalletService.ZERO:
            raise ValueError("Le montant pending a solder doit etre strictement positif")

        def operation():
            balance = WalletService._get_or_create_balance(merchant=merchant, currency=currency)
            WalletService._assert_sufficient(balance.pending_balance, amount, "solde pending insuffisant")
            WalletService._write_entry(
                balance=balance,
                reference=reference,
                operation="pending_clear",
                balance_type="pending",
                direction="debit",
                amount=amount,
                description=description or "Reglement marchand execute",
                context=context,
            )
            WalletService._sync_legacy_fields(merchant)
            return balance

        return WalletTransactionManager.execute(operation)

    @staticmethod
    def transfer(
        *,
        source_merchant: Merchant,
        destination_merchant: Merchant,
        currency: str,
        amount,
        reference: str,
        description: str = None,
        context=None,
    ):
        amount = WalletService._decimal(amount)
        if amount <= WalletService.ZERO:
            raise ValueError("Le montant a transferer doit etre strictement positif")

        def operation():
            WalletService.debit(
                merchant=source_merchant,
                currency=currency,
                amount=amount,
                reference=reference,
                description=description or "Transfert sortant",
                context=context,
            )
            WalletService.credit(
                merchant=destination_merchant,
                currency=currency,
                amount=amount,
                reference=reference,
                description=description or "Transfert entrant",
                context=context,
            )
            return (
                WalletService._get_or_create_balance(merchant=source_merchant, currency=currency),
                WalletService._get_or_create_balance(merchant=destination_merchant, currency=currency),
            )

        return WalletTransactionManager.execute(operation)

    @staticmethod
    def balances_for_merchant(merchant: Merchant):
        rows = (
            MerchantBalance.query
            .filter_by(merchant_id=merchant.id)
            .order_by(MerchantBalance.currency_code.asc())
            .all()
        )
        return [
            {
                "currency": row.currency_code,
                "available_balance": float(row.available_balance or WalletService.ZERO),
                "locked_balance": float(row.locked_balance or WalletService.ZERO),
                "pending_balance": float(row.pending_balance or WalletService.ZERO),
            }
            for row in rows
        ]

    @staticmethod
    def _get_or_create_balance(*, merchant: Merchant, currency: str):
        currency = WalletService._normalize_currency(currency)
        WalletService._ensure_currency(currency)

        balance = MerchantBalance.query.filter_by(
            merchant_id=merchant.id,
            currency_code=currency,
        ).first()
        if balance:
            return balance

        should_seed_legacy = MerchantBalance.query.filter_by(merchant_id=merchant.id).count() == 0
        balance = MerchantBalance(
            merchant_id=merchant.id,
            currency_code=currency,
            available_balance=WalletService.ZERO,
            locked_balance=WalletService.ZERO,
            pending_balance=WalletService.ZERO,
        )
        if should_seed_legacy:
            balance.available_balance = WalletService._decimal(merchant.solde_disponible)
            balance.locked_balance = WalletService._decimal(merchant.solde_verrouille)
        db.session.add(balance)
        db.session.flush()
        return balance

    @staticmethod
    def _write_entry(*, balance: MerchantBalance, reference: str, operation: str, balance_type: str, direction: str, amount: Decimal, description: str = None, context=None):
        current_value = WalletService._decimal(getattr(balance, f"{balance_type}_balance"))
        if direction == "debit":
            updated_value = current_value - amount
        elif direction == "credit":
            updated_value = current_value + amount
        else:
            raise ValueError("Direction de wallet invalide")

        if updated_value < WalletService.ZERO:
            raise ValueError("Le wallet ne peut pas devenir negatif")

        setattr(balance, f"{balance_type}_balance", updated_value)
        db.session.add(
            WalletEntry(
                merchant_id=balance.merchant_id,
                currency_code=balance.currency_code,
                reference=reference,
                operation=operation,
                balance_type=balance_type,
                direction=direction,
                amount=amount,
                before_balance=current_value,
                after_balance=updated_value,
                description=description,
                provider=(context or {}).get("provider") if context else None,
                transaction_id=(context or {}).get("transaction_id") if context else None,
                conversion_id=(context or {}).get("conversion_id") if context else None,
                settlement_id=(context or {}).get("settlement_id") if context else None,
                context=context,
            )
        )

    @staticmethod
    def _sync_legacy_fields(merchant: Merchant):
        balances = MerchantBalance.query.filter_by(merchant_id=merchant.id).all()
        merchant.solde_disponible = float(sum((row.available_balance or WalletService.ZERO) for row in balances))
        merchant.solde_verrouille = float(sum((row.locked_balance or WalletService.ZERO) for row in balances))

    @staticmethod
    def _ensure_currency(currency: str):
        existing = db.session.get(Currency, currency)
        if existing:
            return existing

        default_symbol = {
            "GNF": "FG",
            "CFA": "CFA",
            "XOF": "CFA",
            "USD": "$",
            "EUR": "EUR",
            "CDF": "FC",
        }.get(currency, currency)
        default_decimals = 0 if currency in {"GNF", "CFA", "XOF", "CDF"} else 2
        created = Currency(
            code=currency,
            name=currency,
            symbol=default_symbol,
            decimal_places=default_decimals,
            is_active=True,
        )
        db.session.add(created)
        db.session.flush()
        return created

    @staticmethod
    def _assert_sufficient(current_balance: Decimal, requested_amount: Decimal, message: str):
        if WalletService._decimal(current_balance) < requested_amount:
            raise ValueError(message)

    @staticmethod
    def _normalize_currency(currency: str) -> str:
        if not currency:
            raise ValueError("La devise est obligatoire")
        return str(currency).strip().upper()

    @staticmethod
    def _decimal(value) -> Decimal:
        if value is None:
            return WalletService.ZERO
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
