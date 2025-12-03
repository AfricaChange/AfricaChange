from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from database import db
from models import Rate, Conversion, Utilisateur, CompteSysteme 
from datetime import datetime
import random
import string
from extensions import csrf  # 👈 AJOUT



# 🟢 Le Blueprint doit être défini ici AVANT toute route
convert = Blueprint('convert', __name__, url_prefix='/convert')

# 🔹 Page principale de conversion
@convert.route('/', methods=['GET', 'POST'])
def convertir():
    if request.method == 'POST':
        montant = float(request.form.get('montant'))
        from_currency = request.form.get('from_currency')
        to_currency = request.form.get('to_currency')
        sender_phone = request.form.get('sender_phone')
        receiver_phone = request.form.get('receiver_phone')

        rate = Rate.query.filter_by(from_currency=from_currency, to_currency=to_currency).first()
        if not rate:
            flash("❌ Taux non défini pour cette paire de devises.", "error")
            return redirect(url_for('convert.convertir'))

        montant_converti = round(montant * rate.rate, 2)
        reference = "CVT-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        user_id = session.get('user_id', None)

        nouvelle_conversion = Conversion(
            user_id=user_id,
            from_currency=from_currency,
            to_currency=to_currency,
            montant_initial=montant,
            montant_converti=montant_converti,
            sender_phone=sender_phone,
            receiver_phone=receiver_phone,
            reference=reference,
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

        return render_template(
            'resultat.html',
            montant=montant,
            montant_converti=montant_converti,
            from_currency=from_currency,
            to_currency=to_currency,
            reference=reference,
            sender_phone=sender_phone,
            receiver_phone=receiver_phone,
            taux=rate.rate,
            last_conversions=last_conversions,
            conversion_id=nouvelle_conversion.id
        )

    return render_template('convert.html')


# 🔹 API AJAX (conversion instantanée)
# 🔹 API AJAX (conversion instantanée)
@csrf.exempt   # 👈 AJOUT
@convert.route('/api/convertir', methods=['POST'])
def api_convertir():
    data = request.get_json()
    montant = float(data.get('montant', 0))
    from_currency = data.get('from_currency')
    to_currency = data.get('to_currency')

    rate = Rate.query.filter_by(from_currency=from_currency, to_currency=to_currency).first()
    if not rate:
        return jsonify({"error": "Taux non défini pour cette paire."}), 400

    montant_converti = round(montant * rate.rate, 2)
    return jsonify({"taux": rate.rate, "montant_converti": montant_converti})

# 🔹 Confirmation par référence (avec compte système lié)
@convert.route('/confirmer/<reference>', methods=['POST'])
def confirmer_envoi_par_reference(reference):
    conversion = Conversion.query.filter_by(reference=reference).first()

    if not conversion:
        return jsonify({"error": "Conversion introuvable"}), 404

    if conversion.statut != 'en_attente':
        return jsonify({"error": "Cette conversion a déjà été traitée."}), 400

    try:
        # 🌍 Déterminer le pays cible selon la devise de destination
        mapping_pays = {
            "CFA": "SN",
            "GNF": "GN",
        }
        pays_cible = mapping_pays.get(conversion.to_currency, "SN")

        # 🔍 Trouver un compte système actif correspondant au pays
        compte_systeme = (
            CompteSysteme.query
            .filter_by(pays=pays_cible, actif=True)
            .order_by(CompteSysteme.id.asc())
            .first()
        )

        if not compte_systeme:
            return jsonify({"error": f"Aucun compte système actif trouvé pour le pays {pays_cible}"}), 404

        # ✅ Associer la conversion à ce compte
        conversion.compte_systeme_id = compte_systeme.id

        # 💸 Simulation d’un envoi
        print(f"💸 Envoi simulé via {compte_systeme.nom} : "
              f"{conversion.montant_converti} {conversion.to_currency} "
              f"de {conversion.sender_phone} vers {conversion.receiver_phone}")

        # 🟢 Mise à jour du statut
        conversion.statut = 'envoyée'
        db.session.commit()

        return jsonify({
            "message": f"✅ Envoi de {conversion.montant_converti} {conversion.to_currency} effectué avec succès via {compte_systeme.nom} !",
            "reference": conversion.reference
        }), 200

    except Exception as e:
        conversion.statut = 'échouée'
        db.session.commit()
        return jsonify({"error": f"Erreur lors de l’envoi : {str(e)}"}), 500






# 🔹 Historique des conversions utilisateur (avec pagination + recherche)
@convert.route('/historique')
def historique():
    if not session.get('user_id'):
        flash("Veuillez vous connecter pour voir votre historique.", "warning")
        return redirect(url_for('auth.connexion'))

    user_id = session['user_id']
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    per_page = 10

    query = Conversion.query.filter_by(user_id=user_id)

    # 🔍 Si l’utilisateur recherche un texte
    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Conversion.reference.like(like_pattern),
                Conversion.from_currency.like(like_pattern),
                Conversion.to_currency.like(like_pattern),
                Conversion.sender_phone.like(like_pattern),
                Conversion.receiver_phone.like(like_pattern),
            )
        )

    pagination = query.order_by(Conversion.date_conversion.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return render_template(
        'historique.html',
        conversions=pagination.items,
        pagination=pagination,
        search=search
    )
