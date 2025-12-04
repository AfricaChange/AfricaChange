from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from database import db
from models import Utilisateur, Rate, Compte, Transaction, Conversion, CompteSysteme, Parametre
import io
from datetime import datetime
from openpyxl import Workbook
from io import BytesIO 













admin = Blueprint('admin', __name__, url_prefix='/admin')

# Vérifie si l'utilisateur connecté est admin
def require_admin():
    uid = session.get('user_id')
    if not uid:
        return False
    user = Utilisateur.query.get(uid)
    return bool(user and user.is_admin)

# ============================
# 1️⃣ Tableau de bord principal
# ============================


@admin.route('/dashboard')
def dashboard():
    total_users = Utilisateur.query.count()
    total_transactions = Transaction.query.count()
    total_fonds = db.session.query(db.func.sum(Compte.solde)).scalar() or 0.0
    transactions = Transaction.query.order_by(Transaction.date_transaction.desc()).limit(5).all()

    # 👉 Récupération des taux actuels
    taux_list = Rate.query.all()

    return render_template(
        'admin_dashboard.html',
        total_users=total_users,
        total_transactions=total_transactions,
        total_fonds=total_fonds,
        transactions=transactions,
        taux_list=taux_list
    )


# ============================
# 2️⃣ Gestion des taux
# ============================

@admin.route('/taux', methods=['GET', 'POST'])
def gerer_taux():
    if not require_admin():
        flash("Accès refusé : admin requis.")
        return redirect(url_for('auth.connexion'))

    # Récupération des taux actuels (ou création si absents)
    rate_cfa_gnf = Rate.query.filter_by(from_currency='CFA', to_currency='GNF').first()
    rate_gnf_cfa = Rate.query.filter_by(from_currency='GNF', to_currency='CFA').first()

    if not rate_cfa_gnf:
        rate_cfa_gnf = Rate(from_currency='CFA', to_currency='GNF', rate=14.0)
        db.session.add(rate_cfa_gnf)

    if not rate_gnf_cfa:
        rate_gnf_cfa = Rate(from_currency='GNF', to_currency='CFA', rate=0.07)
        db.session.add(rate_gnf_cfa)
    db.session.commit()

    # Si formulaire soumis
    if request.method == 'POST':
        try:
            cfa_gnf = float(request.form.get('cfa_gnf'))
            gnf_cfa = float(request.form.get('gnf_cfa'))
        except (TypeError, ValueError):
            flash("Veuillez saisir des valeurs numériques valides.")
            return redirect(url_for('admin.gerer_taux'))

        if cfa_gnf <= 0 or gnf_cfa <= 0:
            flash("Les taux doivent être supérieurs à 0.")
            return redirect(url_for('admin.gerer_taux'))

        rate_cfa_gnf.rate = cfa_gnf
        rate_gnf_cfa.rate = gnf_cfa
        db.session.commit()
        flash("✅ Taux mis à jour avec succès.")
        return redirect(url_for('admin.gerer_taux'))

    return render_template('admin_rates.html',
                           rate_cfa_gnf=rate_cfa_gnf,
                           rate_gnf_cfa=rate_gnf_cfa)


# ============================
# 3️⃣ Liste des conversions
# ============================

# 🔹 Liste filtrable des conversions
@admin.route('/conversions')
def export_conversions():
    # 🔐 sécurité : seulement admin
    user_id = session.get("user_id")
    user = None
    if user_id:
        user = Utilisateur.query.get(user_id)
    if not user or not user.is_admin:
        flash("Accès réservé à l’administrateur.", "error")
        return redirect(url_for("auth.connexion"))

    # 🔎 récupérer toutes les conversions
    conversions = (
        Conversion.query
        .order_by(Conversion.date_conversion.desc())
        .all()
    )

    # 📘 création du fichier Excel avec openpyxl
    wb = Workbook()
    ws = wb.active
    ws.title = "Conversions"

    # En-têtes
    headers = [
        "ID",
        "Utilisateur ID",
        "Devise source",
        "Devise cible",
        "Montant initial",
        "Montant converti",
        "Téléphone envoyeur",
        "Téléphone receveur",
        "Référence",
        "Date conversion",
        "Statut",
        "Compte système"
    ]
    ws.append(headers)

    # Lignes
    for c in conversions:
        ws.append([
            c.id,
            c.user_id,
            c.from_currency,
            c.to_currency,
            c.montant_initial,
            c.montant_converti,
            c.sender_phone,
            c.receiver_phone,
            c.reference,
            c.date_conversion.strftime("%Y-%m-%d %H:%M:%S") if c.date_conversion else "",
            c.statut,
            c.compte_systeme.nom if c.compte_systeme else ""
        ])

    # Sauvegarde en mémoire
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"conversions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"

    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    """Exporte toutes les conversions au format Excel (avec comptes système)."""
    

    # Récupération de toutes les conversions
    conversions = Conversion.query.order_by(Conversion.date_conversion.desc()).all()

    # Création du fichier Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Conversions"

    # ✅ En-têtes de colonnes
    ws.append([
        "Référence",
        "Utilisateur",
        "Email utilisateur",
        "De (devise)",
        "Vers (devise)",
        "Montant initial",
        "Montant converti",
        "Téléphone envoyeur",
        "Téléphone récepteur",
        "Statut",
        "Date de conversion",
        "Compte système (nom)",
        "Fournisseur",
        "Pays"
    ])

    # ✅ Remplir les lignes
    for c in conversions:
        utilisateur = Utilisateur.query.get(c.user_id) if c.user_id else None
        compte = c.compte_systeme

        ws.append([
            c.reference or "",
            f"{utilisateur.prenom} {utilisateur.nom}" if utilisateur else "—",
            utilisateur.email if utilisateur else "—",
            c.from_currency or "",
            c.to_currency or "",
            c.montant_initial or 0,
            c.montant_converti or 0,
            c.sender_phone or "",
            c.receiver_phone or "",
            c.statut or "",
            c.date_conversion.strftime("%d/%m/%Y %H:%M") if c.date_conversion else "",
            compte.nom if compte else "—",
            compte.fournisseur if compte else "—",
            compte.pays if compte else "—"
        ])

    # Ajustement automatique de la largeur des colonnes
    for column in ws.columns:
        max_length = max(len(str(cell.value or "")) for cell in column)
        ws.column_dimensions[column[0].column_letter].width = max_length + 2

    # ✅ Envoi du fichier à télécharger
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return send_file(
        file_stream,
        as_attachment=True,
        download_name=f"conversions_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )




# =============================
# 📦 Historique des envois
# =============================

@admin.route("/historique-envois")
def historique_envois():
    page = request.args.get("page", 1, type=int)
    statut = request.args.get("statut", None)

    query = Conversion.query.order_by(Conversion.date_conversion.desc())

    if statut and statut in ["en_attente", "envoyée", "échouée"]:
        query = query.filter_by(statut=statut)

    pagination = query.paginate(page=page, per_page=10, error_out=False)
    conversions = pagination.items

    return render_template(
        "admin_historique.html",
        conversions=conversions,
        pagination=pagination,
        statut=statut
    )




# ===============================================================
# 🏦 GESTION DES COMPTES SYSTÈMES (Wave, Orange Money, etc.)
# ===============================================================


@admin.route('/comptes-systeme', methods=['GET', 'POST'])
def comptes_systeme():
    """Affiche la liste des comptes systèmes + permet d'en ajouter."""
    if request.method == 'POST':
        nom = request.form['nom']
        fournisseur = request.form['fournisseur']
        pays = request.form['pays']
        numero = request.form['numero']

        nouveau_compte = CompteSysteme(
            nom=nom,
            fournisseur=fournisseur,
            pays=pays,
            numero=numero,
            actif=True
        )
        db.session.add(nouveau_compte)
        db.session.commit()
        flash(f"✅ Compte '{nom}' ajouté avec succès.", "success")
        return redirect(url_for('admin.comptes_systeme'))

    comptes = CompteSysteme.query.order_by(CompteSysteme.pays, CompteSysteme.fournisseur).all()
    return render_template('admin_comptes.html', comptes=comptes)


@admin.route('/comptes-systeme/toggle/<int:id>', methods=['POST'])
def toggle_compte(id):
    """Active ou désactive un compte système."""
    compte = CompteSysteme.query.get_or_404(id)
    compte.actif = not compte.actif
    db.session.commit()
    statut = "activé" if compte.actif else "désactivé"
    flash(f"🔄 Compte {compte.nom} {statut}.", "info")
    return redirect(url_for('admin.comptes_systeme'))


@admin.route('/comptes-systeme/supprimer/<int:id>', methods=['POST'])
def supprimer_compte(id):
    """Supprime définitivement un compte système."""
    compte = CompteSysteme.query.get_or_404(id)
    db.session.delete(compte)
    db.session.commit()
    flash(f"🗑️ Compte {compte.nom} supprimé.", "danger")
    return redirect(url_for('admin.comptes_systeme'))





# ===============================================================
# 🏦 ROUTE DE MAINTENANCE
# ===============================================================
@admin.route("/maintenance", methods=["GET", "POST"])
def admin_maintenance():
    # Sécurité : seulement admin
    if not session.get("is_admin"):
        flash("Accès réservé aux administrateurs.", "error")
        return redirect(url_for("main.accueil"))

    # Récupération des paramètres existants
    mode_param = Parametre.query.filter_by(cle="maintenance_mode").first()
    msg_param = Parametre.query.filter_by(cle="maintenance_message").first()

    if request.method == "POST":
        mode = request.form.get("mode", "off")  # "on" ou "off"
        message = request.form.get("message", "").strip()

        if not mode_param:
            mode_param = Parametre(cle="maintenance_mode")
            db.session.add(mode_param)
        mode_param.valeur = "on" if mode == "on" else "off"

        if not msg_param:
            msg_param = Parametre(cle="maintenance_message")
            db.session.add(msg_param)
        msg_param.valeur = message

        db.session.commit()
        flash("Paramètres de maintenance mis à jour ✅", "success")
        return redirect(url_for("admin.admin_maintenance"))

    current_mode = "on" if (mode_param and mode_param.valeur == "on") else "off"
    current_message = msg_param.valeur if msg_param else ""

    return render_template(
        "admin_maintenance.html",
        mode=current_mode,
        message=current_message,
    )