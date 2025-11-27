from flask import Blueprint, render_template, request, flash
from flask import session
from database import db
from models import Rate

exchange = Blueprint('exchange', __name__)


def ensure_default_rates():
    """Crée des taux par défaut si absents (1 CFA = 14 GNF)."""
    r1 = Rate.query.filter_by(from_currency='CFA', to_currency='GNF').first()
    r2 = Rate.query.filter_by(from_currency='GNF', to_currency='CFA').first()
    changed = False
    if not r1:
        r1 = Rate(from_currency='CFA', to_currency='GNF', rate=14.0)
        db.session.add(r1); changed = True
    if not r2:
        r2 = Rate(from_currency='GNF', to_currency='CFA', rate=1/14.0)
        db.session.add(r2); changed = True
    if changed:
        db.session.commit()

@exchange.route('/convertir', methods=['GET', 'POST'])
def convertir():
    # S’assurer que des taux existent
    ensure_default_rates()

    pair = request.form.get('pair', 'CFA_GNF')   # paire sélectionnée
    montant = request.form.get('montant', '')
    resultat = None
    taux_utilise = None

    if request.method == 'POST':
        try:
            val = float(montant)
        except (TypeError, ValueError):
            val = None

        if val is None or val < 0:
            flash("Montant invalide.")
        else:
            if pair == 'CFA_GNF':
                rate = Rate.query.filter_by(from_currency='CFA', to_currency='GNF').first()
                taux_utilise = rate.rate if rate else None
                if taux_utilise:
                    resultat = val * taux_utilise
            else:
                rate = Rate.query.filter_by(from_currency='GNF', to_currency='CFA').first()
                taux_utilise = rate.rate if rate else None
                if taux_utilise:
                    resultat = val * taux_utilise

    # Taux actuels pour affichage
    rate_cfa_gnf = Rate.query.filter_by(from_currency='CFA', to_currency='GNF').first()
    rate_gnf_cfa = Rate.query.filter_by(from_currency='GNF', to_currency='CFA').first()

    return render_template(
        'convert.html',
        pair=pair,
        montant=montant,
        resultat=resultat,
        taux_utilise=taux_utilise,
        rate_cfa_gnf=rate_cfa_gnf,
        rate_gnf_cfa=rate_gnf_cfa,
        is_connected=bool(session.get('user_id'))
    )
