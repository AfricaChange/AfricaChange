import os
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from paiements import paiements_bp
from paiements.models import Depot
from paiements.services import (
    verifier_transaction_unique,
    creer_depot,
    valider_depot_service,
    refuser_depot_service
)
from paiements.models import Retrait
from paiements.services import (
    demander_retrait,
    valider_retrait_service,
    refuser_retrait_service
)
from database import db
from models import Utilisateur  # adapte si ton User est ailleurs
from paiements.services import verifier_fraude
from paiements.utils import admin_required
from convert import convertir




UPLOAD_FOLDER = "static/uploads"


@paiements_bp.route('/depot', methods=['GET', 'POST'])
@login_required
def depot():
    if request.method == 'POST':

        transaction_id = request.form['transaction_id']

        if verifier_transaction_unique(transaction_id):
            flash("Transaction déjà utilisée", "danger")
            return redirect(url_for('paiements.depot'))

        # ✅ récupérer montant AVANT
        montant = float(request.form['montant'])
        taux = get_taux(devise_source, devise_cible)  # adapte selon ton convert.py

        montant_converti = convertir(montant, devise_source, devise_cible)

        profit = montant - montant_converti
        devise_source = request.form.get('devise_source')
        devise_cible = request.form.get('devise_cible')

        # 🔥 TON SYSTEME EXISTANT
        montant_converti = convertir(montant, devise_source, devise_cible)
        
        # ✅ anti-fraude
        etat = verifier_fraude(current_user, montant)

        
        

        # Upload fichier
        fichier = request.files.get('preuve')
        filename = None

        if fichier:
            filename = secure_filename(fichier.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            fichier.save(filepath)

        # Données dépôt
        data = {
            "user_id": current_user.id,
            "numero": request.form['numero'],

            # 🔥 IMPORTANT
            "montant": montant_converti,      # ce que tu envoies
            "montant_source": montant,        # ce que tu reçois

            "devise_source": devise_source,
            "devise_cible": devise_cible,
            
            "taux": taux,
            "profit": profit,

            "transaction_id": transaction_id,
            "methode": request.form['methode'],
            "preuve": filename,
            "statut": "en_attente"
}

        # ✅ appliquer statut anti-fraude
        if etat == "suspect":
            data["statut"] = "suspect"
        elif etat == "verification":
            data["statut"] = "en_verification"

        creer_depot(data)

        flash("Dépôt envoyé, en attente de validation", "info")
        return redirect(url_for('main.dashboard'))  # ⚠️ correction ici

    return render_template('depot.html')


@paiements_bp.route('/admin/depots')
@login_required
@admin_required
def admin_depots():
    depots = Depot.query.order_by(Depot.date.desc()).all()
    return render_template('admin_depots.html', depots=depots)


@paiements_bp.route('/admin/valider/<int:id>')
@login_required
def valider_depot(id):
    depot = Depot.query.get_or_404(id)
    user = User.query.get(depot.user_id)

    valider_depot_service(depot, user)

    flash("Dépôt validé", "success")
    return redirect(url_for('paiements.admin_depots'))

  
    
#DEMANDE UTILISATEUR
@paiements_bp.route('/retrait', methods=['GET', 'POST'])
@login_required
def retrait():
    if request.method == 'POST':
        montant = float(request.form['montant'])

        data = {
            "user_id": current_user.id,
            "numero": request.form['numero'],
            "montant": montant,
            "methode": request.form['methode']
        }

        result = demander_retrait(current_user, data)

        if result == "solde_insuffisant":
            flash("Solde insuffisant", "danger")
        else:
            flash("Demande envoyée", "info")

        return redirect(url_for('dashboard'))

    return render_template('retrait.html')

#ADMIN PANEL
@paiements_bp.route('/admin/retraits')
@login_required
@admin_required
def admin_retraits():
    retraits = Retrait.query.order_by(Retrait.date.desc()).all()
    return render_template('admin_retraits.html', retraits=retraits)
    
#VALIDATION RETRAIT    
@paiements_bp.route('/admin/retrait/valider/<int:id>')
@login_required
@admin_required
def valider_retrait(id):
    retrait = Retrait.query.get_or_404(id)

    valider_retrait_service(retrait)

    flash("Retrait validé", "success")
    return redirect(url_for('paiements.admin_retraits'))
#REFUS
@paiements_bp.route('/admin/retrait/refuser/<int:id>')
@login_required
@admin_required
def refuser_retrait(id):
    retrait = Retrait.query.get_or_404(id)
    user = User.query.get(retrait.user_id)

    refuser_retrait_service(retrait, user)

    flash("Retrait refusé", "danger")
    return redirect(url_for('paiements.admin_retraits'))

@paiements_bp.route('/admin/stats')
@login_required
@admin_required
def stats():
    total_revenus = db.session.query(db.func.sum(Revenu.montant)).scalar() or 0
    total_depots = db.session.query(db.func.sum(Depot.montant)).scalar() or 0

    return render_template(
        'admin_stats.html',
        revenus=total_revenus,
        depots=total_depots
    )    