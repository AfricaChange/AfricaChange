from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash
from database import db
from models import Transaction, Utilisateur, Conversion, Compte
from datetime import datetime
import uuid
from services.orange_money_api import OrangeMoneyAPI
from services.wave_api import WaveAPI







paiement = Blueprint('paiement', __name__, url_prefix='/paiement')


# --------------------------------------------------------
# 🔶 1. INITIER PAIEMENT ORANGE MONEY
# --------------------------------------------------------

@paiement.route('/orange', methods=['POST'])
def paiement_orange():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Veuillez vous connecter"}), 403

    data = request.get_json()
    montant = data.get("montant")
    phone = data.get("telephone")
    reference = data.get("reference")

    if not montant or not phone or not reference:
        return jsonify({"error": "Données incomplètes"}), 400

    om = OrangeMoneyAPI()

    result = om.init_payment(
        amount=montant,
        phone_number=phone,
        return_url=url_for('paiement.orange_callback', _external=True),
        reference=reference
    )

    if not result["success"]:
        return jsonify({"error": result["error"]}), 400

    return jsonify(result["data"])



# --------------------------------------------------------
# 🔶 2. CALLBACK : RETOUR DE OM MONEY
# --------------------------------------------------------
@paiement.route('/orange/callback')
def orange_callback():
    order_id = request.args.get("order_id")

    if not order_id:
        return "Order ID manquant", 400

    om = OrangeMoneyAPI()
    result = om.check_payment_status(order_id)

    if not result["success"]:
        return "Erreur de vérification paiement", 400

    status = result["data"]["status"]

    transaction = Transaction.query.filter_by(reference=order_id).first()

    if not transaction:
        return "Transaction introuvable", 404

    transaction.statut = "valide" if status == "SUCCESS" else "echoue"
    db.session.commit()

    return redirect(url_for('auth.tableau_de_bord'))



# --------------------------------------------------------
# 🔶 3. SIMULATION D’UN PAIEMENT APRES CONVERSION
# --------------------------------------------------------
@paiement.route('/simuler/<int:conversion_id>', methods=['GET'])
def simuler(conversion_id):
    conversion = Conversion.query.get(conversion_id)
    if not conversion:
        flash("Conversion introuvable.", "error")
        return redirect(url_for('convert.convertir'))

    user = Utilisateur.query.get(conversion.user_id) if conversion.user_id else None

    ref = f"PAY-{conversion.reference}"
    transaction = Transaction(
        user_id=conversion.user_id,
        type='paiement',
        montant=conversion.montant_converti,
        statut='valide',
        fournisseur='Simulation',
        reference=ref,
        date_transaction=datetime.utcnow()
    )

    db.session.add(transaction)

    # Créditer le compte utilisateur
    if user:
        compte = Compte.query.filter_by(user_id=user.id).first()
        if not compte:
            compte = Compte(user_id=user.id, solde=0)
            db.session.add(compte)
        compte.solde += conversion.montant_converti

    db.session.commit()

    flash("✅ Paiement simulé avec succès !", "success")

    return render_template(
        "paiement_resultat.html",
        conversion=conversion,
        transaction=transaction,
        user=user
    )


# --------------------------------------------------------
# 🔶 ROUTE DE PAIEMENT WAVE
# --------------------------------------------------------
@paiement.route('/wave', methods=['POST'])
def paiement_wave():
    montant = request.form.get("montant")
    phone = request.form.get("telephone")
    user_id = session.get("user_id")

    if not user_id:
        flash("Veuillez vous connecter pour effectuer un paiement.", "warning")
        return redirect(url_for("auth.connexion"))

    if not montant or not phone:
        flash("Informations de paiement manquantes.", "error")
        return redirect(url_for("convert.convertir"))

    wave = WaveAPI()
    result = wave.create_payment(
        amount=montant,
        currency="XOF",
        return_url=url_for("paiement.wave_callback", _external=True)
    )

    if not result["success"]:
        flash(f"Erreur Wave : {result['error']}", "error")
        return redirect(url_for("convert.convertir"))

    # Enregistre la transaction
    from models import Transaction, Compte
    transaction = Transaction(
        user_id=user_id,
        type="depot",
        montant=float(montant),
        fournisseur="Wave",
        reference=result["data"]["reference"],
        statut="en_attente",
        date_transaction=datetime.utcnow()
    )
    db.session.add(transaction)
    db.session.commit()

    # Redirige vers la page Wave officielle
    return redirect(result["data"]["payment_url"])




# --------------------------------------------------------
# 🔶 callback pour paiement wave 
# --------------------------------------------------------
@paiement.route('/wave/callback')
def wave_callback():
    ref = request.args.get("client_reference")

    if not ref:
        return "Référence manquante", 400

    transaction = Transaction.query.filter_by(reference=ref).first()
    if not transaction:
        return "Transaction introuvable", 404

    # Wave n’envoie pas le statut directement :
    # la réussite du paiement = l'utilisateur est revenu sur success URL
    transaction.statut = "valide"

    db.session.commit()

    flash("Paiement Wave réussi ✅", "success")
    return redirect(url_for("auth.tableau_de_bord"))
