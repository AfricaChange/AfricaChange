from database import db
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from flask import current_app


# ======================================================
# 👤 UTILISATEUR
# ======================================================
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

    # 🔐 Token sécurisé (optionnel – futur email)
    def generate_reset_token(self, expires_sec=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.email, salt='reset-password')

    @staticmethod
    def verify_reset_token(token, expires_sec=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt='reset-password', max_age=expires_sec)
        except Exception:
            return None
        return Utilisateur.query.filter_by(email=email).first()


# ======================================================
# 💱 TAUX DE CHANGE
# ======================================================
class Rate(db.Model):
    __tablename__ = "rate"

    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)
    rate = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('from_currency', 'to_currency', name='uq_rate_pair'),
    )

    def __repr__(self):
        return f"<Rate {self.from_currency}->{self.to_currency}={self.rate}>"


# ======================================================
# 🔁 CONVERSION
# ======================================================
class Conversion(db.Model):
    __tablename__ = "conversion"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)

    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)

    montant_initial = db.Column(db.Float, nullable=False)
    montant_converti = db.Column(db.Float, nullable=False)

    sender_phone = db.Column(db.String(20))
    receiver_phone = db.Column(db.String(20))

    reference = db.Column(db.String(50), unique=True, index=True)
    statut = db.Column(db.String(20), default='en_attente')

    date_conversion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    compte_systeme_id = db.Column(db.Integer, db.ForeignKey('compte_systeme.id'))

    user = db.relationship('Utilisateur', backref='conversions')
    compte_systeme = db.relationship('CompteSysteme', backref='conversions')

    def __repr__(self):
        return f"<Conversion {self.reference} {self.from_currency}->{self.to_currency}>"


# ======================================================
# 👛 COMPTE UTILISATEUR
# ======================================================
class Compte(db.Model):
    __tablename__ = "compte"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), unique=True)
    solde = db.Column(db.Float, default=0.0)
    date_maj = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('Utilisateur', backref=db.backref('compte', uselist=False))

    def __repr__(self):
        return f"<Compte user={self.user_id} solde={self.solde}>"


# ======================================================
# 💳 TRANSACTION
# ======================================================
class Transaction(db.Model):
    __tablename__ = "transaction"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)

    type = db.Column(db.String(20), nullable=False)  # depot / retrait / paiement
    montant = db.Column(db.Float, nullable=False)

    statut = db.Column(db.String(20), default='en_attente')
    fournisseur = db.Column(db.String(50), nullable=False)

    reference = db.Column(db.String(100), unique=True, nullable=False)
    date_transaction = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    user = db.relationship('Utilisateur', backref='transactions')

    def __repr__(self):
        return f"<Transaction {self.fournisseur} {self.montant}>"


# ======================================================
# 💰 PAIEMENT
# ======================================================
class Paiement(db.Model):
    __tablename__ = "paiement"

    id = db.Column(db.Integer, primary_key=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey('conversion.id'), unique=True)

    montant_envoye = db.Column(db.Float, nullable=False)
    montant_recu = db.Column(db.Float, nullable=False)

    devise_source = db.Column(db.String(10), nullable=False)
    devise_cible = db.Column(db.String(10), nullable=False)

    sender_phone = db.Column(db.String(20), nullable=False)
    receiver_phone = db.Column(db.String(20), nullable=False)

    statut = db.Column(db.String(20), default='en_attente')
    date_paiement = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    conversion = db.relationship('Conversion', backref=db.backref('paiement', uselist=False))

    transaction_reference = db.Column(db.String(100), unique=True)


    def __repr__(self):
        return f"<Paiement conversion={self.conversion_id}>"


# ======================================================
# 🏦 COMPTE SYSTÈME
# ======================================================
class CompteSysteme(db.Model):
    __tablename__ = 'compte_systeme'

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


# ======================================================
# ⚙️ PARAMÈTRES SYSTÈME
# ======================================================
class Parametre(db.Model):
    __tablename__ = "parametre"

    id = db.Column(db.Integer, primary_key=True)
    cle = db.Column(db.String(50), unique=True, nullable=False)
    valeur = db.Column(db.String(255))

    def __repr__(self):
        return f"<Parametre {self.cle}={self.valeur}>"


# ======================================================
# 🔐 RESET TOKEN (DB)
# ======================================================
class ResetToken(db.Model):
    __tablename__ = "reset_token"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)

    token = db.Column(db.String(128), unique=True, nullable=False)
    expire_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    user = db.relationship('Utilisateur', backref='reset_tokens')

    def is_valid(self):
        return (not self.used) and self.expire_at > datetime.utcnow()
