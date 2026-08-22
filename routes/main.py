from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from database import db
from models import Conversion, Rate, Transaction
from datetime import datetime
import uuid
from paiements.models import Depot, Retrait, Notification
from flask_login import login_required, current_user
from paiements.services import generer_lien_whatsapp, message_support
from services.homepage_quote_service import (
    DEFAULT_DEMO_AMOUNT,
    build_demo_quote,
    build_quote,
    default_corridor,
    list_supported_corridors,
)








main = Blueprint('main', __name__)

@main.route('/')
def accueil():
    corridors = list_supported_corridors()
    default = default_corridor()

    if default:
        initial_quote = build_quote(
            amount=DEFAULT_DEMO_AMOUNT,
            from_currency=str(default["from_currency"]),
            to_currency=str(default["to_currency"]),
        )
    else:
        initial_quote = build_demo_quote()

    return render_template(
        'index.html',
        minimal_home_shell=True,
        disable_mobile_bottom_nav=True,
        homepage_corridors=corridors,
        homepage_initial_quote=initial_quote,
        homepage_default_amount=DEFAULT_DEMO_AMOUNT,
    )


@main.route('/demarrer-conversion', methods=['POST'])
def demarrer_conversion():
    montant = (request.form.get("montant") or "").strip()
    from_currency = (request.form.get("from_currency") or "").strip().upper()
    to_currency = (request.form.get("to_currency") or "").strip().upper()

    if not montant or not from_currency or not to_currency:
        flash("Veuillez completer le montant et le corridor.", "warning")
        return redirect(url_for("main.accueil"))

    return redirect(
        url_for(
            "convert.convertir",
            montant=montant,
            from_currency=from_currency,
            to_currency=to_currency,
        )
    )


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
#POUR LES ENVOIS MANUELS
@main.route('/dashboard')
@login_required
def dashboard():

    depots = Depot.query.filter_by(user_id=current_user.id)\
        .order_by(Depot.date.desc()).all()

    retraits = Retrait.query.filter_by(user_id=current_user.id)\
        .order_by(Retrait.date.desc()).all()

    notifications = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.date.desc()).all()

    return render_template(
        'dashboard.html',
        depots=depots,
        retraits=retraits,
        notifications=notifications
    )
    


@main.route('/support')
@login_required
def support():

    message = message_support(current_user)

    lien = generer_lien_whatsapp("2246XXXXXXX", message)

    return redirect(lien)    
