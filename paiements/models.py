from datetime import datetime
from database import db

class Depot(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    numero = db.Column(db.String(20))
    montant = db.Column(db.Float)
    transaction_id = db.Column(db.String(100), unique=True)

    methode = db.Column(db.String(50))
    preuve = db.Column(db.String(200))

    statut = db.Column(db.String(50), default="en_attente")

    date = db.Column(db.DateTime, default=datetime.utcnow)
    
    role = db.Column(db.String(20), default="user")  # user / admin

class LogDepot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    depot_id = db.Column(db.Integer)
    action = db.Column(db.String(100))
    admin_id = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    message = db.Column(db.String(255))
    date = db.Column(db.DateTime, default=datetime.utcnow)    
    
class Retrait(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    numero = db.Column(db.String(20))
    montant = db.Column(db.Float)

    methode = db.Column(db.String(50))  # Orange / Wave
    statut = db.Column(db.String(50), default="en_attente")

    reference = db.Column(db.String(100))  # ID paiement admin

    date = db.Column(db.DateTime, default=datetime.utcnow)    
    
class Revenu(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    montant = db.Column(db.Float)
    source = db.Column(db.String(50))  # depot / retrait
    date = db.Column(db.DateTime, default=datetime.utcnow)    