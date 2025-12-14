from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import db
from models import Conversion, Rate
from datetime import datetime
import random

convert = Blueprint('convert', __name__)

@convert.route('/convertir', methods=['GET', 'POST'])
def convertir():
    if request.method == 'POST':
        from_currency = request.form.get('from_currency')
        to_currency = request.form.get('to_currency')
        montant = float(request.form.get('montant'))
        sender_phone = request.form.get('sender_phone')
        receiver_phone = request.form.get('receiver_phone')

        # 🔍 Recherche du taux défini par l’administrateur
        rate = Rate.query.filter_by(from_currency=from_currency, to_currency=to_currency).first()
        if not rate:
            flash("⚠️ Aucun taux défini pour cette paire de devises.")
            return redirect(url_for('convert.convertir'))

        # 💰 Calcul du montant converti
        montant_converti = round(montant * rate.rate, 2)

        # 🎫 Générer une référence unique
        reference = f"TX-{random.randint(100000, 999999)}"

        # 🔐 Récupérer l’utilisateur connecté (s’il y en a un)
        user_id = session.get('user_id') or None

        # 💾 Enregistrer la conversion
        conversion = Conversion(
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
        db.session.add(conversion)
        db.session.commit()

        flash(f"✅ Conversion réussie ! Vous recevrez {montant_converti} {to_currency}.")
        return redirect(url_for('convert.resultat', ref=reference))

    return render_template('convert.html')


@convert.route('/resultat/<ref>')
def resultat(ref):
    conversion = Conversion.query.filter_by(reference=ref).first()
    if not conversion:
        flash("❌ Aucune conversion trouvée avec cette référence.")
        return redirect(url_for('convert.convertir'))

    return render_template('resultat.html', conversion=conversion)
