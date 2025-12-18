from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template, flash
from database import db
from models import Transaction, Utilisateur, Conversion, Compte, Paiement
from datetime import datetime
import uuid
from extensions import csrf
from services.payment_service import PaymentService
from services.providers.orange_provider import OrangeProvider
from services.providers.wave_provider import WaveProvider
from services.callbacks import CallbackManager



paiement = Blueprint('paiement', __name__, url_prefix='/paiement')



# ======================================================
# 🔶 ORANGE MONEY – INITIATION DE PAIEMENT
# ======================================================


@paiement.route('/orange', methods=['POST'])
@csrf.exempt
def paiement_orange():
    data = request.get_json(silent=True) or {}

    reference = data.get("reference")
    telephone = data.get("telephone")
    montant = float(data.get("montant", 0))

    try:
        # 🔒 1) Lock DB
        conversion = PaymentService.lock_conversion(reference)

        # 🔐 2) Provider Orange
        provider = OrangeProvider()
        result = provider.init_payment(
            amount=montant,
            phone=telephone,
            reference=conversion.reference,
            return_url=url_for("paiement.orange_callback", _external=True)
        )

        # 🧾 3) Traces internes
        transaction = PaymentService.create_transaction(
            conversion,
            fournisseur="Orange Money",
            montant=montant
        )

        PaymentService.create_paiement(
            conversion,
            transaction.reference,
            telephone
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "payment_url": result["payment_url"]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400



# --------------------------------------------------------
# 🔶 2. CALLBACK : RETOUR DE OM MONEY
# --------------------------------------------------------

@paiement.route('/orange/callback')
def orange_callback():
    reference = request.args.get("order_id")
    ip = request.remote_addr

    if not reference:
        return "Référence manquante", 400

    try:
        provider = OrangeProvider()
        status = provider.check_status(reference)

        tx = CallbackManager.validate(
            reference=reference,
            provider="Orange Money",
            payload=status,
            ip=ip
        )

        tx.statut = "valide" if status.get("status") == "SUCCESS" else "echoue"

        db.session.commit()
        return redirect(url_for("auth.tableau_de_bord"))

    except Exception as e:
        db.session.rollback()
        return f"Erreur callback: {str(e)}", 403




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

@paiement.route('/wave', methods=['POST'])
@csrf.exempt
def paiement_wave():
    data = request.get_json(silent=True) or {}

    reference = data.get("reference")
    telephone = data.get("telephone")
    montant = float(data.get("montant", 0))

    try:
        conversion = PaymentService.lock_conversion(reference)

        provider = WaveProvider()
        provider_result = provider.create_payment(
            amount=montant,
            reference=conversion.reference,
            return_url=url_for("paiement.wave_callback", _external=True)
        )

        transaction = PaymentService.create_transaction(
            conversion,
            fournisseur="Wave",
            montant=montant
        )

        PaymentService.create_paiement(
            conversion,
            transaction.reference,
            telephone
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "payment_url": provider_result["payment_url"]
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400





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











