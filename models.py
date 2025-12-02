from database import db
from datetime import datetime

class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telephone = db.Column(db.String(20), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    def __repr__(self):
        return f"<Utilisateur {self.nom} {self.prenom}>"

class Rate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)
    rate = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('from_currency', 'to_currency', name='uq_pair'),
    )

    def __repr__(self):
        return f"<Rate {self.from_currency}->{self.to_currency}={self.rate}>"

class Conversion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=True)
    from_currency = db.Column(db.String(10))
    to_currency = db.Column(db.String(10))
    montant_initial = db.Column(db.Float, nullable=False)
    montant_converti = db.Column(db.Float, nullable=False)
    sender_phone = db.Column(db.String(20))
    receiver_phone = db.Column(db.String(20))
    reference = db.Column(db.String(50), unique=True, nullable=True)
    date_conversion = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    statut = db.Column(db.String(20), default='en_attente')
    compte_systeme_id = db.Column(db.Integer, db.ForeignKey('compte_systeme.id'), nullable=True)

    # relationships
    compte_systeme = db.relationship('CompteSysteme', backref='conversions', lazy=True)
    user = db.relationship('Utilisateur', backref='conversions', lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.date_conversion:
            self.date_conversion = datetime.utcnow()

    def __repr__(self):
        return f"<Conversion {self.from_currency}->{self.to_currency}: {self.montant_initial}→{self.montant_converti}>"

class Compte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    solde = db.Column(db.Float, default=0.0)
    date_maj = db.Column(db.DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('Utilisateur', backref='compte', uselist=False)

    def __repr__(self):
        return f"<Compte utilisateur={self.user_id}, solde={self.solde}>"

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'depot' ou 'retrait' ou 'envoi'
    montant = db.Column(db.Float, nullable=False)
    statut = db.Column(db.String(20), default='en_attente')  # 'en_attente', 'valide', 'echoue'
    reference = db.Column(db.String(100), unique=True, nullable=False)
    fournisseur = db.Column(db.String(50), nullable=False)  # 'Wave', 'Orange Money', ...
    date_transaction = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    user = db.relationship('Utilisateur', backref='transactions')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.date_transaction:
            self.date_transaction = datetime.utcnow()

    def __repr__(self):
        return f"<Transaction {self.fournisseur} {self.type} {self.montant}>"

class Paiement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversion_id = db.Column(db.Integer, db.ForeignKey('conversion.id'))
    montant_envoye = db.Column(db.Float, nullable=False)
    montant_recu = db.Column(db.Float, nullable=False)
    devise_source = db.Column(db.String(10), nullable=False)
    devise_cible = db.Column(db.String(10), nullable=False)
    sender_phone = db.Column(db.String(20), nullable=False)
    receiver_phone = db.Column(db.String(20), nullable=False)
    statut = db.Column(db.String(20), default="en_attente")  # 'en_attente' / 'succès' / 'échec'
    date_paiement = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    conversion = db.relationship("Conversion", backref="paiement", uselist=False)

    def __repr__(self):
        return f"<Paiement {self.sender_phone} -> {self.receiver_phone} : {self.montant_envoye}>"

class CompteSysteme(db.Model):
    __tablename__ = 'compte_systeme'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    fournisseur = db.Column(db.String(50), nullable=False)
    pays = db.Column(db.String(10), nullable=False)
    numero = db.Column(db.String(20), nullable=False, unique=True)
    actif = db.Column(db.Boolean, default=True)
    solde = db.Column(db.Float, default=0.0)
    date_creation = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    def __repr__(self):
        return f"<CompteSysteme {self.fournisseur} {self.pays}>"
