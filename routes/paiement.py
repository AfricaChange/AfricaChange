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
from services.security.ip_whitelist import IPWhitelist
from services.ledger_service import LedgerService
from services.risk_engine import RiskEngine
from services.alert_service import AlertService
import services.constants as constants








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

    if not reference or not telephone:
        return jsonify({"error": "Données manquantes"}), 400

    try:
        # 🔒 1) Lock conversion
        conversion = PaymentService.lock_conversion(reference)
        montant = conversion.montant_initial

        # 🔐 2) Provider
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

@paiement.route('/orange/callback', methods=["POST", "GET"])
def orange_callback():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = ip.split(",")[0].strip()  # 🔐 sécurité proxy

    raw_payload = request.get_data(as_text=True)
    payload = request.get_json(silent=True) or {}
    headers = request.headers

    reference = payload.get("order_id") or request.args.get("order_id")

    if not reference:
        return "Référence manquante", 400

    # 🔒 1️⃣ IP ALLOWLIST
    if not IPWhitelist.is_allowed("orange", ip):
        return "IP non autorisée", 403

    try:
        provider = OrangeProvider()

        # 🔐 2️⃣ Signature cryptographique
        if not provider.verify_callback(raw_payload, headers):
            return "Callback Orange invalide (signature)", 403

        nonce = provider.extract_nonce(payload, headers)

        # 🛡️ 3️⃣ Anti-replay / idempotence
        tx = CallbackManager.validate(
            reference=reference,
            provider="Orange Money",
            payload=payload,
            ip=ip
        )

        # 📊 4️⃣ Risk scoring
        risk_score = RiskEngine.score_transaction(tx, ip)

        if risk_score >= RiskEngine.HIGH_RISK:
            RiskEngine.log(
                reference=reference,
                provider="Orange Money",
                ip=ip,
                risk_type="high_risk_transaction",
                score=risk_score,
                details="Risque élevé détecté"
            )
            AlertService.critical(
                f"🚨 Transaction BLOQUÉE {reference} – score {risk_score}"
            )
            raise ValueError("Transaction bloquée pour risque élevé")

        elif risk_score >= RiskEngine.MEDIUM_RISK:
            RiskEngine.log(
                reference=reference,
                provider="Orange Money",
                ip=ip,
                risk_type="medium_risk",
                score=risk_score,
                details="Transaction sous surveillance"
            )
            AlertService.warning(
                f"⚠️ Transaction suspecte {reference} – score {risk_score}"
            )

        # 📦 5️⃣ Validation métier
        if not provider.is_valid_status(payload):
            raise ValueError("Statut Orange non reconnu")

        tx.statut = "valide" if payload.get("status") == "SUCCESS" else "echoue"

        # 💰 6️⃣ Ledger (double écriture)
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

    if not reference or not telephone:
        return jsonify({"error": "Données manquantes"}), 400

    try:
        # 🔒 1) Lock conversion
        conversion = PaymentService.lock_conversion(reference)
        montant = conversion.montant_initial

        # 🔐 2) Provider
        provider = WaveProvider()
        provider_result = provider.create_payment(
            amount=montant,
            reference=conversion.reference,
            return_url=url_for("paiement.wave_callback", _external=True)
        )

        # 🧾 3) Traces internes
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
@paiement.route('/wave/callback', methods=["GET"])
def wave_callback():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = ip.split(",")[0].strip()

    payload = request.args.to_dict()
    reference = payload.get("client_reference")

    if not reference:
        return "Référence manquante", 400

    try:
        provider = WaveProvider()

        # 🛡️ 1️⃣ Anti-replay / antifraud
        tx = CallbackManager.validate(
            reference=reference,
            provider="Wave",
            payload=payload,
            ip=ip
        )

        # 📊 2️⃣ Risk scoring
        risk_score = RiskEngine.score_transaction(tx, ip)

        if risk_score >= RiskEngine.HIGH_RISK:
            RiskEngine.log(
                reference=reference,
                provider="Wave",
                ip=ip,
                risk_type="high_risk_transaction",
                score=risk_score,
                details="Risque élevé détecté"
            )
            AlertService.critical(
                f"🚨 Transaction Wave BLOQUÉE {reference} – score {risk_score}"
            )
            raise ValueError("Transaction bloquée")

        tx.statut =PaymentStatus
        

        # 💰 Ledger pour debit utilisateur
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
        # credit compte systeme
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

        flash("Paiement Wave réussi ✅", "success")
        return redirect(url_for("auth.tableau_de_bord"))

    except Exception as e:
        db.session.rollback()
        return f"Erreur callback Wave: {str(e)}", 403


