from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from database import db
from models import Rate, Conversion, Utilisateur, CompteSysteme
from datetime import datetime
import random
import string
from extensions import csrf
from sqlalchemy import or_

# 🟢 Blueprint
convert = Blueprint('convert', __name__, url_prefix='/convert')

MAX_PUBLIC_AMOUNT = 500000  # 500 000 CFA max pour non connectés

# ======================================================
# 🔹 PAGE PRINCIPALE DE CONVERSION
# ======================================================
@convert.route('/', methods=['GET', 'POST'])
def convertir():
    if request.method == 'POST':
        try:
            montant = float(request.form.get('montant', 0))
            user_id = session.get('user_id')

            # 🔐 Limitation pour utilisateurs non connectés
            if not user_id and montant > MAX_PUBLIC_AMOUNT:
                flash(
                      f"Pour convertir plus de {MAX_PUBLIC_AMOUNT:,} CFA, veuillez vous connecter.",
                     "warning"
                )
                return redirect(url_for('auth.connexion'))

        except ValueError:
            flash("Montant invalide.", "error")
            return redirect(url_for('convert.convertir'))

        if montant <= 0:
            flash("Le montant doit être supérieur à 0.", "warning")
            return redirect(url_for('convert.convertir'))

        from_currency = request.form.get('from_currency')
        to_currency = request.form.get('to_currency')
        sender_phone = request.form.get('sender_phone')
        receiver_phone = request.form.get('receiver_phone')

        if not all([from_currency, to_currency, sender_phone, receiver_phone]):
            flash("Tous les champs sont obligatoires.", "warning")
            return redirect(url_for('convert.convertir'))

        rate = Rate.query.filter_by(
            from_currency=from_currency,
            to_currency=to_currency
        ).first()

        if not rate:
            flash("❌ Taux non défini pour cette paire de devises.", "error")
            return redirect(url_for('convert.convertir'))

        montant_converti = round(montant * rate.rate, 2)

        reference = "CVT-" + ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )

        user_id = session.get('user_id')

        nouvelle_conversion = Conversion(
            user_id=user_id,
            from_currency=from_currency,
            to_currency=to_currency,
            montant_initial=montant,
            montant_converti=montant_converti,
            sender_phone=sender_phone,
            receiver_phone=receiver_phone,
            reference=reference,
            statut='en_attente',
            date_conversion=datetime.utcnow()
        )

        db.session.add(nouvelle_conversion)
        db.session.commit()

        last_conversions = []
        if user_id:
            last_conversions = (
                Conversion.query
                .filter_by(user_id=user_id)
                .order_by(Conversion.date_conversion.desc())
                .limit(3)
                .all()
            )

        flash(f"✅ Conversion réussie ! Référence : {reference}", "success")

        return redirect(
               url_for('convert.recap', reference=reference)
        )


    return render_template('convert.html')


# ======================================================
# 🔹 API AJAX – CONVERSION INSTANTANÉE
# ======================================================
@csrf.exempt  # volontaire : endpoint JS interne
@convert.route('/api/convertir', methods=['POST'])
def api_convertir():
    data = request.get_json(silent=True) or {}

    try:
        montant = float(data.get('montant', 0))
    except ValueError:
        return jsonify({"error": "Montant invalide"}), 400

    if montant <= 0:
        return jsonify({"error": "Montant invalide"}), 400

    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')

    rate = Rate.query.filter_by(
        from_currency=from_currency,
        to_currency=to_currency
    ).first()

    if not rate:
        return jsonify({"error": "Taux non défini pour cette paire."}), 400

    montant_converti = round(montant * rate.rate, 2)

    return jsonify({
        "taux": rate.rate,
        "montant_converti": montant_converti
    })


# ======================================================
# 🔹 CONFIRMATION PAR RÉFÉRENCE (COMPTE SYSTÈME)
# ======================================================
@convert.route('/confirmer/<reference>', methods=['POST'])
def confirmer_envoi_par_reference(reference):
    conversion = Conversion.query.filter_by(reference=reference).first()

    if not conversion:
        return jsonify({"error": "Conversion introuvable"}), 404

    if conversion.statut != 'en_attente':
        return jsonify({"error": "Conversion déjà traitée."}), 400

    try:
        mapping_pays = {
            "CFA": "SN",
            "GNF": "GN",
        }
        pays_cible = mapping_pays.get(conversion.to_currency)

        compte_systeme = (
            CompteSysteme.query
            .filter_by(pays=pays_cible, actif=True)
            .order_by(CompteSysteme.id.asc())
            .first()
        )

        if not compte_systeme:
            return jsonify({"error": "Aucun compte système actif disponible"}), 404

        conversion.compte_systeme_id = compte_systeme.id

        # ✅ STATUT NORMALISÉ
        conversion.statut = 'paiement_en_cours'

        db.session.commit()

        return jsonify({
            "message": f"✅ Paiement en cours via {compte_systeme.nom}",
            "reference": conversion.reference
        }), 200

    except Exception:
        conversion.statut = 'echoue'
        db.session.commit()
        return jsonify({"error": "Erreur lors du traitement"}), 500



# ======================================================
# 🔹 HISTORIQUE UTILISATEUR (PAGINATION + RECHERCHE)
# ======================================================
@convert.route('/historique')
def historique():
    if not session.get('user_id'):
        flash("Veuillez vous connecter.", "warning")
        return redirect(url_for('auth.connexion'))

    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    per_page = 10

    query = Conversion.query.filter(
        Conversion.user_id == user_id,
        Conversion.statut.in_([
            "en_attente",
            "paiement_en_cours",
            "valide",
            "echoue"
        ])
    )


    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Conversion.reference.like(like),
                Conversion.from_currency.like(like),
                Conversion.to_currency.like(like),
                Conversion.sender_phone.like(like),
                Conversion.receiver_phone.like(like),
            )
        )

    pagination = query.order_by(
        Conversion.date_conversion.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'historique.html',
        conversions=pagination.items,
        pagination=pagination,
        search=search
    )

@convert.route('/recap/<reference>')
def recap(reference):
    conversion = Conversion.query.filter_by(reference=reference).first()

    if not conversion:
        flash("Conversion introuvable.", "danger")
        return redirect(url_for('convert.convertir'))

    # Sécurité : empêcher accès à une conversion d’un autre utilisateur
    if conversion.user_id:
       if conversion.user_id != session.get("user_id"):
         flash("Accès non autorisé.", "danger")
         return redirect(url_for('main.accueil'))
 

    return render_template(
        "recap.html",
        conversion=conversion
    )
