from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash
from database import db
from models import Transaction, Utilisateur, Conversion, Compte, Paiement
from datetime import datetime
import uuid
from services.orange_money_api import OrangeMoneyAPI
from services.wave_api import WaveAPI
from extensions import csrf






paiement = Blueprint('paiement', __name__, url_prefix='/paiement')



# ======================================================
# 🔶 ORANGE MONEY – INITIATION DE PAIEMENT
# ======================================================
@csrf.exempt  # endpoint JS / API interne
@paiement.route('/orange', methods=['POST'])
def paiement_orange():
    data = request.get_json(silent=True) or {}

    try:
        montant = float(data.get('montant', 0))
    except ValueError:
        return jsonify({"error": "Montant invalide"}), 400

    telephone = data.get('telephone')
    reference = data.get('reference')

    if not all([montant, telephone, reference]):
        return jsonify({"error": "Données manquantes"}), 400

    if montant <= 0:
        return jsonify({"error": "Montant incorrect"}), 400

    conversion = Conversion.query.filter_by(reference=reference).first()
    if not conversion:
        return jsonify({"error": "Conversion introuvable"}), 404

    if conversion.statut != 'en_attente':
        return jsonify({"error": "Conversion déjà traitée"}), 400
    # 🔐 Sécurité : empêcher paiement d’une conversion d’un autre utilisateur
    if conversion.user_id is not None:
       if conversion.user_id != session.get("user_id"):
          return jsonify({"error": "Action non autorisée"}), 403

    try:
        # 🔒 Bloquer double paiement
        conversion.statut = "paiement_en_cours"
        db.session.commit()

        paiement = Paiement(
            conversion_id=conversion.id,
            montant_envoye=conversion.montant_initial,
            montant_recu=conversion.montant_converti,
            devise_source=conversion.from_currency,
            devise_cible=conversion.to_currency,
            sender_phone=telephone,
            receiver_phone=conversion.receiver_phone,
            statut='en_attente',
            date_paiement=datetime.utcnow()
        )

        db.session.add(paiement)

        transaction = Transaction(
            user_id=conversion.user_id,
            type='paiement',
            montant=montant,
            statut='en_attente',
            fournisseur='Orange Money',
            reference=str(uuid.uuid4())[:12],
            date_transaction=datetime.utcnow()
        )

        db.session.add(transaction)
        # 🔗 Lien Paiement ↔ Transaction (audit)
        paiement.transaction_reference = transaction.reference

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Paiement Orange Money initié avec succès.",
            "reference": transaction.reference
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de l’initiation du paiement"}), 500



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


# ======================================================
# 🌊 WAVE – INITIATION DE PAIEMENT
# ======================================================
@csrf.exempt
@paiement.route('/wave', methods=['POST'])
def paiement_wave():
    data = request.get_json(silent=True) or {}

    try:
        montant = float(data.get('montant', 0))
    except ValueError:
        return jsonify({"error": "Montant invalide"}), 400

    telephone = data.get('telephone')
    reference = data.get('reference')

    if not all([montant, telephone, reference]):
        return jsonify({"error": "Données manquantes"}), 400

    if montant <= 0:
        return jsonify({"error": "Montant incorrect"}), 400

    conversion = Conversion.query.filter_by(reference=reference).first()
    if not conversion:
        return jsonify({"error": "Conversion introuvable"}), 404

    if conversion.statut != 'en_attente':
        return jsonify({"error": "Conversion déjà traitée"}), 400
    # 🔐 Sécurité : empêcher paiement d’une conversion d’un autre utilisateur
    if conversion.user_id is not None:
       if conversion.user_id != session.get("user_id"):
          return jsonify({"error": "Action non autorisée"}), 403

    try:
        # 🔒 Bloquer double paiement
        conversion.statut = "paiement_en_cours"
        db.session.commit()

        paiement = Paiement(
            conversion_id=conversion.id,
            montant_envoye=conversion.montant_initial,
            montant_recu=conversion.montant_converti,
            devise_source=conversion.from_currency,
            devise_cible=conversion.to_currency,
            sender_phone=telephone,
            receiver_phone=conversion.receiver_phone,
            statut='en_attente',
            date_paiement=datetime.utcnow()
        )

        db.session.add(paiement)

        transaction = Transaction(
            user_id=conversion.user_id,
            type='paiement',
            montant=montant,
            statut='en_attente',
            fournisseur='Wave',
            reference=str(uuid.uuid4())[:12],
            date_transaction=datetime.utcnow()
        )

        db.session.add(transaction)
        # 🔗 Lien Paiement ↔ Transaction (audit)
        paiement.transaction_reference = transaction.reference

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Paiement Wave initié avec succès.",
            "reference": transaction.reference
        }), 200

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Erreur lors de l’initiation du paiement"}), 500



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











