from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from database import db
from models import Conversion, Rate, Transaction
from datetime import datetime
import uuid
main = Blueprint('main', __name__)

@main.route('/')
def accueil():
    return render_template('index.html')


@main.route('/conversion', methods=['GET', 'POST'])
def conversion():
    taux_cfa_gnf = Rate.query.filter_by(from_currency='CFA', to_currency='GNF').first()
    taux_gnf_cfa = Rate.query.filter_by(from_currency='GNF', to_currency='CFA').first()

    montant_converti = None

    if request.method == 'POST':
        try:
            from_currency = request.form['from_currency']
            to_currency = request.form['to_currency']
            montant = float(request.form['montant'])
            sender_phone = request.form['sender_phone']
            receiver_phone = request.form['receiver_phone']

            # Vérification de la paire et conversion
            if from_currency == 'CFA' and to_currency == 'GNF':
                montant_converti = montant * taux_cfa_gnf.rate
            elif from_currency == 'GNF' and to_currency == 'CFA':
                montant_converti = montant * taux_gnf_cfa.rate
            else:
                flash("La paire de devise sélectionnée est invalide.")
                return redirect(url_for('main.conversion'))

            # Enregistrement de la conversion
            conv = Conversion(
                user_id=session.get('user_id'),
                from_currency=from_currency,
                to_currency=to_currency,
                montant_initial=montant,
                montant_converti=montant_converti,
                sender_phone=sender_phone,
                receiver_phone=receiver_phone,
                reference=str(uuid.uuid4())[:10],
                date_conversion=datetime.utcnow()
            )
            db.session.add(conv)
            db.session.commit()

            flash("✅ Conversion simulée avec succès !")
        except Exception as e:
            flash(f"Erreur : {e}")

    return render_template('conversion.html',
                           taux_cfa_gnf=taux_cfa_gnf,
                           taux_gnf_cfa=taux_gnf_cfa,
                           montant_converti=montant_converti)
