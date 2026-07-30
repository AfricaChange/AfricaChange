"""Primary SQLAlchemy model registry for the historical Flask application.

EPIC 9.R5 keeps this module monolithic on purpose. The current refactor only
clarifies its role and prepares a future split by aggregate without modifying
schema or runtime behaviour.
"""

import json
from datetime import datetime
from decimal import Decimal
from hashlib import sha256

from flask import current_app
from itsdangerous import URLSafeTimedSerializer

from database import db
from services.constants import PaymentStatus


class Utilisateur(db.Model):
    __tablename__ = "utilisateur"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    telephone = db.Column(db.String(20), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Utilisateur {self.id} {self.email}>"

    def generate_reset_token(self, expires_sec=3600):
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        return serializer.dumps(self.email, salt="reset-password")

    @staticmethod
    def verify_reset_token(token, expires_sec=3600):
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        try:
            email = serializer.loads(
                token,
                salt="reset-password",
                max_age=expires_sec,
            )
        except Exception:
            return None
        return Utilisateur.query.filter_by(email=email).first()


class AdminUser(db.Model):
    __tablename__ = "admin_user"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), unique=True)
    role = db.Column(db.String(20))
    actif = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AdminAction(db.Model):
    __tablename__ = "admin_action"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_user.id"))
    action_type = db.Column(db.String(50))
    target_type = db.Column(db.String(50))
    target_reference = db.Column(db.String(100))
    reason = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Rate(db.Model):
    __tablename__ = "rate"

    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)
    rate = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("from_currency", "to_currency", name="uq_rate_pair"),
    )

    def __repr__(self):
        return f"<Rate {self.from_currency}->{self.to_currency}={self.rate}>"


class Merchant(db.Model):
    __tablename__ = "merchant"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(40), unique=True, nullable=False, index=True)
    nom = db.Column(db.String(120), nullable=False)
    telephone = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    pays = db.Column(db.String(10), nullable=False)

    actif = db.Column(db.Boolean, default=True, nullable=False)
    verifie = db.Column(db.Boolean, default=False, nullable=False)
    risk_score = db.Column(db.Integer, default=0, nullable=False)
    suspended_at = db.Column(db.DateTime(timezone=True), nullable=True)
    suspension_reason = db.Column(db.String(255), nullable=True)

    solde_disponible = db.Column(db.Float, default=0.0, nullable=False)
    solde_verrouille = db.Column(db.Float, default=0.0, nullable=False)

    min_ticket = db.Column(db.Float, default=0.0, nullable=False)
    max_ticket = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def can_handle(self, amount: float) -> bool:
        if amount <= 0 or not self.actif or not self.verifie:
            return False
        if amount < (self.min_ticket or 0.0):
            return False
        if self.max_ticket is not None and amount > self.max_ticket:
            return False
        return self.solde_disponible >= amount

    def can_handle_currency(self, currency: str, amount) -> bool:
        amount = Decimal(str(amount or 0))
        if amount <= 0 or not self.actif or not self.verifie:
            return False
        if amount < Decimal(str(self.min_ticket or 0.0)):
            return False
        if self.max_ticket is not None and amount > Decimal(str(self.max_ticket)):
            return False

        balance = MerchantBalance.query.filter_by(
            merchant_id=self.id,
            currency_code=currency,
        ).first()
        if balance:
            return balance.available_balance >= amount

        return Decimal(str(self.solde_disponible or 0.0)) >= amount

    def __repr__(self):
        return f"<Merchant {self.code} {self.nom}>"


class MerchantRate(db.Model):
    __tablename__ = "merchant_rate"

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False)
    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)
    rate = db.Column(db.Float, nullable=False)
    actif = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    merchant = db.relationship("Merchant", backref="rates")

    __table_args__ = (
        db.UniqueConstraint(
            "merchant_id",
            "from_currency",
            "to_currency",
            name="uq_merchant_rate_pair",
        ),
    )

    def __repr__(self):
        return (
            f"<MerchantRate merchant={self.merchant_id} "
            f"{self.from_currency}->{self.to_currency}={self.rate}>"
        )


class Settlement(db.Model):
    __tablename__ = "settlement"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(60), unique=True, nullable=False, index=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey("conversion.id"), nullable=False, unique=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False)

    gross_amount = db.Column(db.Float, nullable=False)
    platform_fee = db.Column(db.Float, nullable=False, default=0.0)
    net_amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    notes = db.Column(db.String(255), nullable=True)
    approved_by_admin_id = db.Column(db.Integer, db.ForeignKey("admin_user.id"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    settled_at = db.Column(db.DateTime(timezone=True), nullable=True)

    conversion = db.relationship("Conversion", backref=db.backref("settlement", uselist=False))
    merchant = db.relationship("Merchant", backref="settlements")

    def __repr__(self):
        return f"<Settlement {self.reference} {self.status}>"


class Dispute(db.Model):
    __tablename__ = "dispute"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(60), unique=True, nullable=False, index=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transaction.id"), nullable=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey("conversion.id"), nullable=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=True)

    reason = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="open")
    opened_by_admin_id = db.Column(db.Integer, db.ForeignKey("admin_user.id"), nullable=True)
    resolved_by_admin_id = db.Column(db.Integer, db.ForeignKey("admin_user.id"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)

    transaction = db.relationship("Transaction", backref="disputes")
    conversion = db.relationship("Conversion", backref="disputes")
    merchant = db.relationship("Merchant", backref="disputes")

    def __repr__(self):
        return f"<Dispute {self.reference} {self.status}>"


class Conversion(db.Model):
    __tablename__ = "conversion"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=True)

    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)

    montant_initial = db.Column(db.Float, nullable=False)
    montant_converti = db.Column(db.Float, nullable=False)

    sender_phone = db.Column(db.String(20))
    receiver_phone = db.Column(db.String(20))

    reference = db.Column(db.String(50), unique=True, index=True)
    statut = db.Column(db.String(50), default=PaymentStatus.EN_ATTENTE.value)
    date_conversion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    # Le mode hybride trace explicitement qui porte la liquidite et le risque.
    liquidity_source_type = db.Column(db.String(20), default="platform", nullable=False)
    risk_bearer = db.Column(db.String(20), default="platform", nullable=False)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=True)
    merchant_rate_id = db.Column(db.Integer, db.ForeignKey("merchant_rate.id"), nullable=True)
    assigned_rate = db.Column(db.Float, nullable=True)
    platform_fee = db.Column(db.Float, default=0.0, nullable=False)
    locked_amount = db.Column(db.Float, default=0.0, nullable=False)
    settlement_status = db.Column(db.String(20), default="pending", nullable=False)
    reserved_until = db.Column(db.DateTime(timezone=True), nullable=True)
    selection_reason = db.Column(db.String(255), nullable=True)
    quote_source_amount = db.Column(db.Numeric(24, 8), nullable=True)
    quote_target_amount = db.Column(db.Numeric(24, 8), nullable=True)
    client_rate = db.Column(db.Numeric(24, 8), nullable=True)
    decision_code = db.Column(db.String(50), nullable=True)
    execution_mode = db.Column(db.String(20), nullable=True)
    reservation_reference = db.Column(db.String(100), nullable=True, index=True)
    margin_estimated = db.Column(db.Numeric(24, 8), nullable=True)
    quote_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    accepted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    offer_snapshot = db.Column(db.JSON, nullable=True)
    decision_snapshot = db.Column(db.JSON, nullable=True)
    execution_snapshot = db.Column(db.JSON, nullable=True)
    compte_systeme_id = db.Column(db.Integer, db.ForeignKey("compte_systeme.id"))

    user = db.relationship("Utilisateur", backref="conversions")
    compte_systeme = db.relationship("CompteSysteme", backref="conversions")
    merchant = db.relationship("Merchant", backref="conversions")
    merchant_rate = db.relationship("MerchantRate", backref="conversions")

    @property
    def liquidity_label(self):
        if self.liquidity_source_type == "merchant" and self.merchant:
            return f"Marchand: {self.merchant.nom}"
        if self.compte_systeme:
            return f"Plateforme: {self.compte_systeme.nom}"
        return "Plateforme"

    def __repr__(self):
        return f"<Conversion {self.reference} {self.from_currency}->{self.to_currency}>"


class Compte(db.Model):
    __tablename__ = "compte"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), unique=True)
    solde = db.Column(db.Float, default=0.0)
    date_maj = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = db.relationship("Utilisateur", backref=db.backref("compte", uselist=False))

    def __repr__(self):
        return f"<Compte user={self.user_id} solde={self.solde}>"


class Transaction(db.Model):
    __tablename__ = "transaction"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    statut = db.Column(db.String(20), default=PaymentStatus.EN_ATTENTE.value)
    fournisseur = db.Column(db.String(50), nullable=False)
    reference = db.Column(db.String(100), unique=True, nullable=False)
    date_transaction = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    user = db.relationship("Utilisateur", backref="transactions")

    def __repr__(self):
        return f"<Transaction {self.fournisseur} {self.montant}>"


class Paiement(db.Model):
    __tablename__ = "paiement"

    id = db.Column(db.Integer, primary_key=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey("conversion.id"), unique=True)

    montant_envoye = db.Column(db.Float, nullable=False)
    montant_recu = db.Column(db.Float, nullable=False)

    devise_source = db.Column(db.String(10), nullable=False)
    devise_cible = db.Column(db.String(10), nullable=False)

    sender_phone = db.Column(db.String(20), nullable=False)
    receiver_phone = db.Column(db.String(20), nullable=False)

    statut = db.Column(db.String(20), default=PaymentStatus.EN_ATTENTE.value)
    date_paiement = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    conversion = db.relationship("Conversion", backref=db.backref("paiement", uselist=False))

    transaction_reference = db.Column(db.String(100), unique=True)
    idempotency_key = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    def __repr__(self):
        return f"<Paiement conversion={self.conversion_id}>"


class CompteSysteme(db.Model):
    __tablename__ = "compte_systeme"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    fournisseur = db.Column(db.String(50), nullable=False)
    pays = db.Column(db.String(10), nullable=False)
    numero = db.Column(db.String(20), unique=True, nullable=False)

    actif = db.Column(db.Boolean, default=True)
    solde = db.Column(db.Float, default=0.0)
    date_creation = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f"<CompteSysteme {self.fournisseur} {self.pays}>"


class Parametre(db.Model):
    __tablename__ = "parametre"

    id = db.Column(db.Integer, primary_key=True)
    cle = db.Column(db.String(50), unique=True, nullable=False)
    valeur = db.Column(db.String(255))

    def __repr__(self):
        return f"<Parametre {self.cle}={self.valeur}>"


class Currency(db.Model):
    __tablename__ = "currency"

    code = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    decimal_places = db.Column(db.Integer, nullable=False, default=2)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f"<Currency {self.code}>"


class MerchantBalance(db.Model):
    __tablename__ = "merchant_balance"

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False, index=True)
    currency_code = db.Column(db.String(10), db.ForeignKey("currency.code"), nullable=False, index=True)
    available_balance = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    locked_balance = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    pending_balance = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    merchant = db.relationship("Merchant", backref="wallet_balances")
    currency = db.relationship("Currency", backref="merchant_balances")

    __table_args__ = (
        db.UniqueConstraint("merchant_id", "currency_code", name="uq_merchant_balance_currency"),
    )

    def __repr__(self):
        return f"<MerchantBalance merchant={self.merchant_id} {self.currency_code}>"


class WalletEntry(db.Model):
    __tablename__ = "wallet_entry"

    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False, index=True)
    currency_code = db.Column(db.String(10), db.ForeignKey("currency.code"), nullable=False, index=True)
    reference = db.Column(db.String(100), nullable=False, index=True)
    operation = db.Column(db.String(30), nullable=False)
    balance_type = db.Column(db.String(20), nullable=False)
    direction = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(24, 8), nullable=False)
    before_balance = db.Column(db.Numeric(24, 8), nullable=False)
    after_balance = db.Column(db.Numeric(24, 8), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    provider = db.Column(db.String(50), nullable=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transaction.id"), nullable=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey("conversion.id"), nullable=True)
    settlement_id = db.Column(db.Integer, db.ForeignKey("settlement.id"), nullable=True)
    context = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    merchant = db.relationship("Merchant", backref="wallet_entries")
    currency = db.relationship("Currency", backref="wallet_entries")
    settlement = db.relationship("Settlement", backref="wallet_entries")

    def __repr__(self):
        return f"<WalletEntry {self.operation} {self.amount} {self.currency_code}>"


class ResetToken(db.Model):
    __tablename__ = "reset_token"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False)
    token = db.Column(db.String(128), unique=True, nullable=False)
    expire_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    user = db.relationship("Utilisateur", backref="reset_tokens")

    def is_valid(self):
        return (not self.used) and self.expire_at > datetime.utcnow()


class PaymentEvent(db.Model):
    __tablename__ = "payment_event"

    id = db.Column(db.Integer, primary_key=True)
    transaction_reference = db.Column(db.String(100), index=True)
    provider = db.Column(db.String(50))
    event_type = db.Column(db.String(50))
    payload = db.Column(db.JSON)
    ip_address = db.Column(db.String(45))
    nonce = db.Column(db.String(128), unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            "transaction_reference",
            "event_type",
            "provider",
            name="uq_event_once",
        ),
    )

    def __repr__(self):
        return f"<PaymentEvent {self.provider} {self.event_type}>"


class LedgerEntry(db.Model):
    __tablename__ = "ledger_entry"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), index=True, nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transaction.id"), nullable=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey("conversion.id"), nullable=True)
    paiement_id = db.Column(db.Integer, db.ForeignKey("paiement.id"), nullable=True)
    compte = db.Column(db.String(50), nullable=False)
    sens = db.Column(db.String(6), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    devise = db.Column(db.String(10), nullable=False)
    provider = db.Column(db.String(50))
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Ledger {self.sens} {self.montant} {self.devise} {self.compte}>"


class RiskEvent(db.Model):
    __tablename__ = "risk_event"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), index=True)
    provider = db.Column(db.String(50))
    ip_address = db.Column(db.String(50))
    risk_type = db.Column(db.String(50))
    risk_score = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(db.Integer, primary_key=True)
    actor_type = db.Column(db.String(20))
    actor_id = db.Column(db.Integer, nullable=True)
    event = db.Column(db.String(100))
    payload = db.Column(db.JSON)
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AdminWalletAction(db.Model):
    __tablename__ = "admin_wallet_action"

    id = db.Column(db.Integer, primary_key=True)
    requested_by_admin_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False, index=True)
    approved_by_admin_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=True, index=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey("merchant.id"), nullable=False, index=True)
    currency_code = db.Column(db.String(10), db.ForeignKey("currency.code"), nullable=False, index=True)
    action = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(24, 8), nullable=False)
    reference = db.Column(db.String(100), nullable=False, unique=True, index=True)
    reason = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(50), nullable=True)
    session_identifier = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="completed")
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    merchant = db.relationship("Merchant", backref="admin_wallet_actions")
    currency = db.relationship("Currency", backref="admin_wallet_actions")

    def __repr__(self):
        return f"<AdminWalletAction {self.action} {self.reference}>"


class ExecutionReservation(db.Model):
    __tablename__ = "execution_reservation"

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(100), nullable=False, unique=True, index=True)
    transaction_reference = db.Column(db.String(100), nullable=False, unique=True, index=True)
    mode_execution = db.Column(db.String(20), nullable=False)
    devise = db.Column(db.String(10), nullable=False, index=True)
    montant_total = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    montant_platform = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    montant_merchant = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    montant_provider = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    sources = db.Column(db.JSON, nullable=False, default=list)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    consumed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    released_at = db.Column(db.DateTime(timezone=True), nullable=True)
    failure_reason = db.Column(db.String(255), nullable=True)

    def __repr__(self):
        return f"<ExecutionReservation {self.reference} {self.status}>"


class ConversionExecution(db.Model):
    __tablename__ = "conversion_execution"

    id = db.Column(db.Integer, primary_key=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey("conversion.id"), nullable=False, unique=True, index=True)
    execution_reference = db.Column(db.String(100), nullable=False, unique=True, index=True)
    mode = db.Column(db.String(20), nullable=False)
    provider_code = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=False, index=True)
    payin_reference = db.Column(db.String(100), nullable=True)
    payout_reference = db.Column(db.String(100), nullable=True)
    payin_status = db.Column(db.String(50), nullable=True)
    payout_status = db.Column(db.String(50), nullable=True)
    amount_source = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    amount_destination = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    provider_fees = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    execution_cost = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    payin_cost_real = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    payout_cost_real = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    provider_cost_real = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    execution_cost_real = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    error_code = db.Column(db.String(50), nullable=True)
    error_message = db.Column(db.String(255), nullable=True)
    raw_context = db.Column(db.JSON, nullable=True)
    started_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    conversion = db.relationship("Conversion", backref=db.backref("execution", uselist=False))

    def __repr__(self):
        return f"<ConversionExecution {self.execution_reference} {self.status}>"


class MerchantExecutionLease(db.Model):
    __tablename__ = "merchant_execution_lease"

    id = db.Column(db.Integer, primary_key=True)
    lease_reference = db.Column(db.String(100), nullable=False, unique=True, index=True)
    execution_id = db.Column(
        db.Integer,
        db.ForeignKey("conversion_execution.id"),
        nullable=False,
        index=True,
    )
    merchant_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant.id"),
        nullable=False,
        index=True,
    )
    assignment_reference = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    released_at = db.Column(db.DateTime(timezone=True), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)

    execution = db.relationship(
        "ConversionExecution",
        backref=db.backref("merchant_execution_leases", lazy=True),
    )
    merchant = db.relationship(
        "Merchant",
        backref=db.backref("merchant_execution_leases", lazy=True),
    )

    __mapper_args__ = {
        "version_id_col": version,
        "version_id_generator": lambda version: 1 if version is None else version + 1,
    }

    def __repr__(self):
        return f"<MerchantExecutionLease {self.lease_reference} {self.status}>"


class MerchantPool(db.Model):
    __tablename__ = "merchant_pool"

    id = db.Column(db.Integer, primary_key=True)
    pool_reference = db.Column(db.String(100), nullable=False, unique=True, index=True)
    nom = db.Column(db.String(120), nullable=False)
    corridor = db.Column(db.String(50), nullable=False, index=True)
    source_currency = db.Column(db.String(10), nullable=False, index=True)
    target_currency = db.Column(db.String(10), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="active", index=True)
    priority = db.Column(db.Integer, nullable=False, default=100)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return f"<MerchantPool {self.pool_reference} {self.corridor}>"


class MerchantPoolMembership(db.Model):
    __tablename__ = "merchant_pool_membership"

    id = db.Column(db.Integer, primary_key=True)
    membership_reference = db.Column(
        db.String(100), nullable=False, unique=True, index=True
    )
    pool_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant_pool.id"),
        nullable=False,
        index=True,
    )
    merchant_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant.id"),
        nullable=False,
        index=True,
    )
    priority = db.Column(db.Integer, nullable=False, default=100, index=True)
    enabled = db.Column(db.Boolean, nullable=False, default=True, index=True)
    joined_at = db.Column(db.DateTime(timezone=True), nullable=False)
    left_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    pool = db.relationship(
        "MerchantPool",
        backref=db.backref("memberships", lazy=True),
    )
    merchant = db.relationship(
        "Merchant",
        backref=db.backref("pool_memberships", lazy=True),
    )

    __table_args__ = (
        db.Index(
            "uq_merchant_pool_membership_active",
            "pool_id",
            "merchant_id",
            unique=True,
            sqlite_where=db.text("enabled = 1"),
            postgresql_where=db.text("enabled = true"),
        ),
    )

    def __repr__(self):
        return (
            f"<MerchantPoolMembership {self.membership_reference} "
            f"pool={self.pool_id} merchant={self.merchant_id}>"
        )


class MerchantExecutionDecision(db.Model):
    __tablename__ = "merchant_execution_decision"

    id = db.Column(db.Integer, primary_key=True)
    decision_reference = db.Column(db.String(100), nullable=False, unique=True, index=True)
    execution_id = db.Column(
        db.Integer,
        db.ForeignKey("conversion_execution.id"),
        nullable=False,
        index=True,
    )
    lease_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant_execution_lease.id"),
        nullable=True,
    )
    pool_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant_pool.id"),
        nullable=True,
    )
    selected_merchant_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant.id"),
        nullable=False,
        index=True,
    )
    decision_status = db.Column(db.String(20), nullable=False, index=True)
    decision_reason = db.Column(db.String(255), nullable=False)
    trust_score = db.Column(db.Numeric(24, 8), nullable=True)
    estimated_cost = db.Column(db.Numeric(24, 8), nullable=True)
    timeout_applied = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    execution = db.relationship(
        "ConversionExecution",
        backref=db.backref("merchant_execution_decisions", lazy=True),
    )
    lease = db.relationship(
        "MerchantExecutionLease",
        backref=db.backref("merchant_execution_decisions", lazy=True),
    )
    pool = db.relationship(
        "MerchantPool",
        backref=db.backref("merchant_execution_decisions", lazy=True),
    )
    selected_merchant = db.relationship(
        "Merchant",
        backref=db.backref("merchant_execution_decisions", lazy=True),
    )

    def __repr__(self):
        return (
            f"<MerchantExecutionDecision {self.decision_reference} "
            f"{self.decision_status}>"
        )


class MerchantExecutionAssignment(db.Model):
    __tablename__ = "merchant_execution_assignment"

    id = db.Column(db.Integer, primary_key=True)
    assignment_reference = db.Column(
        db.String(100), nullable=False, unique=True, index=True
    )
    execution_id = db.Column(
        db.Integer,
        db.ForeignKey("conversion_execution.id"),
        nullable=False,
        index=True,
    )
    merchant_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant.id"),
        nullable=False,
        index=True,
    )
    pool_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant_pool.id"),
        nullable=True,
        index=True,
    )
    slice_reference = db.Column(db.String(100), nullable=False)
    source_currency = db.Column(db.String(10), nullable=False)
    target_currency = db.Column(db.String(10), nullable=False)
    source_amount = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    target_amount = db.Column(db.Numeric(24, 8), nullable=False, default=Decimal("0"))
    status = db.Column(db.String(30), nullable=False, index=True)
    offered_at = db.Column(db.DateTime(timezone=True), nullable=True)
    accepted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    refused_at = db.Column(db.DateTime(timezone=True), nullable=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    execution = db.relationship(
        "ConversionExecution",
        backref=db.backref("merchant_execution_assignments", lazy=True),
    )
    merchant = db.relationship(
        "Merchant",
        backref=db.backref("merchant_execution_assignments", lazy=True),
    )
    pool = db.relationship(
        "MerchantPool",
        backref=db.backref("merchant_execution_assignments", lazy=True),
    )

    __mapper_args__ = {
        "version_id_col": version,
        "version_id_generator": lambda version: 1 if version is None else version + 1,
    }

    def __repr__(self):
        return (
            f"<MerchantExecutionAssignment {self.assignment_reference} "
            f"{self.status}>"
        )


class MerchantExecutionEvent(db.Model):
    __tablename__ = "merchant_execution_event"

    id = db.Column(db.Integer, primary_key=True)
    event_reference = db.Column(
        db.String(100), nullable=False, unique=True, index=True
    )
    execution_id = db.Column(
        db.Integer,
        db.ForeignKey("conversion_execution.id"),
        nullable=False,
        index=True,
    )
    assignment_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant_execution_assignment.id"),
        nullable=True,
        index=True,
    )
    lease_id = db.Column(
        db.Integer,
        db.ForeignKey("merchant_execution_lease.id"),
        nullable=True,
        index=True,
    )
    event_type = db.Column(db.String(50), nullable=False, index=True)
    event_source = db.Column(db.String(50), nullable=False)
    event_payload = db.Column(db.JSON, nullable=True)
    correlation_id = db.Column(db.String(100), nullable=False, index=True)
    occurred_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    execution = db.relationship(
        "ConversionExecution",
        backref=db.backref("merchant_execution_events", lazy=True),
    )
    assignment = db.relationship(
        "MerchantExecutionAssignment",
        backref=db.backref("merchant_execution_events", lazy=True),
    )
    lease = db.relationship(
        "MerchantExecutionLease",
        backref=db.backref("merchant_execution_events", lazy=True),
    )

    def __repr__(self):
        return f"<MerchantExecutionEvent {self.event_reference} {self.event_type}>"


class MerchantTransactionRecord(db.Model):
    __tablename__ = "merchant_transaction_record"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(
        db.String(100), nullable=False, unique=True, index=True
    )
    current_state = db.Column(db.String(50), nullable=False, index=True)
    current_occurred_at = db.Column(db.DateTime(timezone=True), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    last_correlation_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __mapper_args__ = {
        "version_id_col": version,
        "version_id_generator": lambda version: 1 if version is None else version + 1,
    }

    def __repr__(self):
        return (
            f"<MerchantTransactionRecord {self.transaction_id} "
            f"{self.current_state} v{self.version}>"
        )


class MerchantTransactionTransitionEvent(db.Model):
    __tablename__ = "merchant_transaction_transition_event"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), nullable=False, index=True)
    previous_state = db.Column(db.String(50), nullable=False)
    resulting_state = db.Column(db.String(50), nullable=False)
    transition_decision = db.Column(db.String(30), nullable=False, index=True)
    occurred_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    correlation_id = db.Column(db.String(100), nullable=False, index=True)
    reason = db.Column(db.String(255), nullable=False)
    event_reference = db.Column(
        db.String(100), nullable=False, unique=True, index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<MerchantTransactionTransitionEvent {self.event_reference} "
            f"{self.transition_decision}>"
        )


class MerchantDeliveryRecord(db.Model):
    __tablename__ = "merchant_delivery_record"

    id = db.Column(db.Integer, primary_key=True)
    provider_message_id = db.Column(
        db.String(120), nullable=False, unique=True, index=True
    )
    channel = db.Column(db.String(30), nullable=False, index=True)
    current_state = db.Column(db.String(30), nullable=False, index=True)
    current_occurred_at = db.Column(db.DateTime(timezone=True), nullable=True)
    failure_code = db.Column(db.String(80), nullable=True)
    failure_reason = db.Column(db.String(255), nullable=True)
    version = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __mapper_args__ = {
        "version_id_col": version,
        "version_id_generator": lambda version: 1 if version is None else version + 1,
    }

    def __repr__(self):
        return (
            f"<MerchantDeliveryRecord {self.provider_message_id} "
            f"{self.current_state} v{self.version}>"
        )


class MerchantDeliveryReceiptEvent(db.Model):
    __tablename__ = "merchant_delivery_receipt_event"

    id = db.Column(db.Integer, primary_key=True)
    provider_message_id = db.Column(db.String(120), nullable=False, index=True)
    previous_state = db.Column(db.String(30), nullable=False)
    resulting_state = db.Column(db.String(30), nullable=False)
    transition_decision = db.Column(db.String(30), nullable=False, index=True)
    receipt_status = db.Column(db.String(30), nullable=False, index=True)
    receipt_occurred_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    failure_code = db.Column(db.String(80), nullable=True)
    failure_reason = db.Column(db.String(255), nullable=True)
    correlation_id = db.Column(db.String(100), nullable=False, index=True)
    event_reference = db.Column(
        db.String(100), nullable=False, unique=True, index=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<MerchantDeliveryReceiptEvent {self.event_reference} "
            f"{self.transition_decision}>"
        )


class ExecutionProof(db.Model):
    __tablename__ = "execution_proof"

    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.Integer, db.ForeignKey("conversion_execution.id"), nullable=False, index=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey("conversion.id"), nullable=False, index=True)
    stage = db.Column(db.String(30), nullable=False, index=True)
    proof_type = db.Column(db.String(50), nullable=False)
    external_reference = db.Column(db.String(100), nullable=True, index=True)
    file_path = db.Column(db.String(255), nullable=True)
    issuer = db.Column(db.String(120), nullable=True)
    proof_date = db.Column(db.DateTime(timezone=True), nullable=True)
    proof_hash = db.Column(db.String(64), nullable=False, index=True)
    validated_by_admin_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=False, index=True)
    validated_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    validation_status = db.Column(db.String(20), nullable=False, default="validated", index=True)
    review_comment = db.Column(db.String(255), nullable=True)
    reviewed_by_admin_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=True, index=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    execution = db.relationship("ConversionExecution", backref="proofs")
    conversion = db.relationship("Conversion", backref="execution_proofs")
    validated_by = db.relationship("Utilisateur", foreign_keys=[validated_by_admin_id])
    reviewed_by = db.relationship("Utilisateur", foreign_keys=[reviewed_by_admin_id])

    @staticmethod
    def build_hash(payload) -> str:
        normalized = json.dumps(payload or {}, sort_keys=True, ensure_ascii=True, default=str)
        return sha256(normalized.encode("utf-8")).hexdigest()

    def __repr__(self):
        return f"<ExecutionProof {self.stage} {self.proof_type} {self.external_reference or self.id}>"


class ExecutionAudit(db.Model):
    __tablename__ = "execution_audit"

    id = db.Column(db.Integer, primary_key=True)
    execution_id = db.Column(db.Integer, db.ForeignKey("conversion_execution.id"), nullable=False, index=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey("conversion.id"), nullable=False, index=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("utilisateur.id"), nullable=True, index=True)
    actor_type = db.Column(db.String(20), nullable=False, default="system")
    action = db.Column(db.String(50), nullable=False, index=True)
    comment = db.Column(db.String(255), nullable=True)
    proof_id = db.Column(db.Integer, db.ForeignKey("execution_proof.id"), nullable=True, index=True)
    ip_address = db.Column(db.String(50), nullable=True)
    payload = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    execution = db.relationship("ConversionExecution", backref="audits")
    conversion = db.relationship("Conversion", backref="execution_audits")
    actor = db.relationship("Utilisateur", foreign_keys=[actor_id])
    proof = db.relationship("ExecutionProof", foreign_keys=[proof_id])

    def __repr__(self):
        return f"<ExecutionAudit {self.action} {self.execution_id}>"


class Refund(db.Model):
    __tablename__ = "refund"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transaction.id"))
    amount = db.Column(db.Float)
    reason = db.Column(db.Text)
    admin_id = db.Column(db.Integer, db.ForeignKey("admin_user.id"))
    status = db.Column(
        db.String(20),
        default=PaymentStatus.EN_ATTENTE.value,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
