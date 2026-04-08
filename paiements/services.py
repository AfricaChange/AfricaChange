from paiements.models import Depot, LogDepot
from database import db

def verifier_transaction_unique(transaction_id):
    return Depot.query.filter_by(transaction_id=transaction_id).first()

FRAIS_DEPOT = 0.02  # 2%

def calculer_frais(montant, taux):
    return montant * taux 

def creer_depot(data):
    montant = data["montant"]

    frais = calculer_frais(montant, FRAIS_DEPOT)
    montant_net = montant - frais

    data["montant"] = montant_net

    depot = Depot(**data)

    db.session.add(depot)
    db.session.commit()

    enregistrer_revenu(frais)

    return depot


def log_action(depot_id, action, admin_id=None):
    log = LogDepot(
        depot_id=depot_id,
        action=action,
        admin_id=admin_id
    )
    db.session.add(log)
    db.session.commit()


def valider_depot_service(depot, user):
    if depot.statut != "en_attente":
        return False

    depot.statut = "valide"
    user.solde += depot.montant

    db.session.commit()

    log_action(depot.id, "valide", user.id)
    # ✅ ICI on notifie
    notifier(user.id, "Votre dépôt a été validé")
    return True
    
   


def refuser_depot_service(depot):
    depot.statut = "refuse"
    db.session.commit()
    log_action(depot.id, "refuse")
    notifier(depot.user_id, "Votre dépôt a été refusé")
    
def marquer_en_verification(depot):
    depot.statut = "en_verification"
    db.session.commit()
    log_action(depot.id, "verification")


def marquer_suspect(depot):
    depot.statut = "suspect"
    db.session.commit()
    log_action(depot.id, "suspect")

#Anti_Fraude

def verifier_fraude(user, montant):
    # règle simple
    if montant > 10000000:  # à adapter
        return "suspect"

    depots_recents = Depot.query.filter_by(user_id=user.id)\
        .order_by(Depot.date.desc()).limit(5).all()

    if len(depots_recents) >= 3:
        return "verification"

    return "ok"    
    
def notifier(user_id, message):
    notif = Notification(user_id=user_id, message=message)
    db.session.add(notif)
    db.session.commit()   
    
FRAIS_RETRAIT = 0.03  # 3%   
   
def demander_retrait(user, data):
    frais = calculer_frais(data["montant"], FRAIS_RETRAIT)
    montant_total = data["montant"] + frais

    if user.solde < montant_total:
     return "solde_insuffisant"
    # 🔥 bloquer le montant immédiatement
    user.solde -= montant_total

    enregistrer_revenu(frais)

    retrait = Retrait(**data)

    

    db.session.add(retrait)
    db.session.commit()

    notifier(user.id, "Votre demande de retrait est en attente")

    return retrait
    
def valider_retrait_service(retrait):
    if retrait.statut != "en_attente":
        return False

    retrait.statut = "valide"
    db.session.commit()

    notifier(retrait.user_id, "Votre retrait a été effectué")

    return True    
    
def refuser_retrait_service(retrait, user):
    retrait.statut = "refuse"

    # 🔥 rembourser
    user.solde += retrait.montant

    db.session.commit()

    notifier(user.id, "Votre retrait a été refusé")    
    
def enregistrer_revenu(montant, source="depot"):
    revenu = Revenu(montant=montant, source=source)
    db.session.add(revenu)
    db.session.commit()    