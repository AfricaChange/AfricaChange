from flask import Blueprint, request, jsonify, redirect, url_for, render_template, flash
from database import db
from models import Transaction, Utilisateur, Conversion, Compte
from datetime import datetime
from extensions import csrf

from services.payment_service import PaymentService
from services.providers.orange_provider import OrangeProvider
from services.providers.wave_provider import WaveProvider
from services.callbacks import CallbackManager
from services.security.ip_whitelist import IPWhitelist
from services.ledger_service import LedgerService
from services.risk_engine import RiskEngine
from services.alert_service import AlertService
from services.constants import PaymentStatus


paiement = Blueprint('paiement', __name__, url_prefix='/paiement')

# ======================================================
# 🔶 ORANGE MONEY – route de controle
# ======================================================
@paiement.route("/init", methods=["POST"])
@csrf.exempt
def init_paiement():
    data = request.get_json(silent=True) or {}

    provider = data.get("provider")
    reference = data.get("reference")
    phone = data.get("phone")

    if not provider or not reference or not phone:
        return jsonify({"error": "Données manquantes"}), 400

    conversion = Conversion.query.filter_by(reference=reference).first()
    if not conversion:
        return jsonify({"error": "Conversion introuvable"}), 404

    try:
        if provider == "orange":
            orange = OrangeProvider()
            result = orange.init_payment(
                amount=conversion.montant_initial,
                phone=phone,
                reference=conversion.reference,
                return_url=url_for("paiement.orange_callback", _external=True)
            )
            return jsonify({"success": True, **result})

        return jsonify({"error": "Provider non supporté"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ======================================================
# 🔶 ORANGE MONEY – INITIATION
# ======================================================
@paiement.route('/orange', methods=['POST'])
@csrf.exempt
def paiement_orange():
    data = request.get_json(silent=True) or {}

    reference = data.get("reference")
    telephone = data.get("telephone")

    if not reference or not telephone:
        return jsonify({"error": "Données manquantes"}), 400

    try:
        conversion = PaymentService.lock_conversion(reference)
        montant = conversion.montant_initial

        provider = OrangeProvider()
        result = provider.init_payment(
            amount=montant,
            phone=telephone,
            reference=conversion.reference,
            return_url=url_for("paiement.orange_callback", _external=True)
        )

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
        return jsonify({"success": True, "payment_url": result["payment_url"]})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ======================================================
# 🔶 ORANGE CALLBACK
# ======================================================
@paiement.route('/orange/callback', methods=["POST", "GET"])
def orange_callback():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = ip.split(",")[0].strip()

    raw_payload = request.get_data(as_text=True)
    payload = request.get_json(silent=True) or {}
    headers = request.headers

    reference = payload.get("order_id") or request.args.get("order_id")
    if not reference:
        return "Référence manquante", 400

    if not IPWhitelist.is_allowed("orange", ip):
        return "IP non autorisée", 403

    try:
        provider = OrangeProvider()

        if not provider.verify_callback(raw_payload, headers):
            return "Signature Orange invalide", 403

        tx = CallbackManager.validate(
            reference=reference,
            provider="Orange Money",
            payload=payload,
            ip=ip
        )

        risk_score = RiskEngine.score_transaction(tx, ip)
        if risk_score >= RiskEngine.HIGH_RISK:
            AlertService.critical(f"🚨 Transaction bloquée {reference}")
            tx.statut = PaymentStatus.BLOQUE.value
            db.session.commit()
            return "Transaction bloquée", 403

        if not provider.is_valid_status(payload):
            raise ValueError("Statut Orange inconnu")

        orange_status = payload.get("status")

        provider = OrangeProvider()
        tx.statut = provider.map_status(orange_status)


        LedgerService.record(
            reference=tx.reference,
            compte="user_wallet",
            sens="debit",
            montant=tx.montant,
            devise="XOF",
            provider=tx.fournisseur,
            transaction_id=tx.id,
            description="Paiement utilisateur"
        )

        LedgerService.record(
            reference=tx.reference,
            compte=f"system_{tx.fournisseur.lower()}",
            sens="credit",
            montant=tx.montant,
            devise="XOF",
            provider=tx.fournisseur,
            transaction_id=tx.id,
            description="Encaissement système"
        )

        db.session.commit()
        return redirect(url_for("auth.tableau_de_bord"))

    except Exception as e:
        db.session.rollback()
        return f"Erreur callback Orange: {str(e)}", 403


# ======================================================
# 🔶 SIMULATION
# ======================================================
@paiement.route('/simuler/<int:conversion_id>')
def simuler(conversion_id):
    conversion = Conversion.query.get_or_404(conversion_id)

    ref = f"SIM-{conversion.reference}"
    tx = Transaction(
        user_id=conversion.user_id,
        type="paiement",
        montant=conversion.montant_converti,
        statut=PaymentStatus.VALIDE.value,
        fournisseur="Simulation",
        reference=ref,
        date_transaction=datetime.utcnow()
    )

    db.session.add(tx)
    db.session.commit()

    flash("Paiement simulé avec succès", "success")
    return render_template("paiement_resultat.html", conversion=conversion, transaction=tx)


# ======================================================
# 🌊 WAVE – INITIATION
# ======================================================
@paiement.route('/wave', methods=['POST'])
@csrf.exempt
def paiement_wave():
    data = request.get_json(silent=True) or {}

    reference = data.get("reference")
    telephone = data.get("telephone")

    if not reference or not telephone:
        return jsonify({"error": "Données manquantes"}), 400

    try:
        conversion = PaymentService.lock_conversion(reference)
        montant = conversion.montant_initial

        provider = WaveProvider()
        result = provider.create_payment(
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
        return jsonify({"success": True, "payment_url": result["payment_url"]})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# ======================================================
# 🌊 WAVE CALLBACK
# ======================================================
@paiement.route('/wave/callback', methods=["GET"])
def wave_callback():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = ip.split(",")[0].strip()

    payload = request.args.to_dict()
    reference = payload.get("client_reference")
    if not reference:
        return "Référence manquante", 400

    try:
        tx = CallbackManager.validate(
            reference=reference,
            provider="Wave",
            payload=payload,
            ip=ip
        )

        risk_score = RiskEngine.score_transaction(tx, ip)
        if risk_score >= RiskEngine.HIGH_RISK:
            tx.statut = PaymentStatus.BLOQUE.value
            db.session.commit()
            return "Transaction Wave bloquée", 403

        tx.statut = PaymentStatus.VALIDE.value

        LedgerService.record(
            reference=tx.reference,
            compte="user_wallet",
            sens="debit",
            montant=tx.montant,
            devise="XOF",
            provider=tx.fournisseur,
            transaction_id=tx.id,
            description="Paiement utilisateur"
        )

        LedgerService.record(
            reference=tx.reference,
            compte=f"system_{tx.fournisseur.lower()}",
            sens="credit",
            montant=tx.montant,
            devise="XOF",
            provider=tx.fournisseur,
            transaction_id=tx.id,
            description="Encaissement système"
        )

        db.session.commit()
        flash("Paiement Wave réussi", "success")
        return redirect(url_for("auth.tableau_de_bord"))

    except Exception as e:
        db.session.rollback()
        return f"Erreur callback Wave: {str(e)}", 403
