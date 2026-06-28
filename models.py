from datetime import datetime
from decimal import Decimal

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
    statut = db.Column(db.String(20), default=PaymentStatus.EN_ATTENTE.value)
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
