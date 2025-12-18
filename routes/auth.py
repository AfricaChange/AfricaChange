from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import (
    Utilisateur,
    Compte,
    Transaction,
    Conversion,
    ResetToken
)
from datetime import datetime, timedelta
import uuid

from flask_limiter.util import get_remote_address
from extensions import limiter

auth = Blueprint('auth', __name__)


# ============================
# 🔹1 INSCRIPTION
# ============================
@auth.route('/inscription', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def inscription():
    if request.method == 'POST':
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        email = request.form.get('email')
        telephone = request.form.get('telephone')
        mot_de_passe = request.form.get('mot_de_passe')

        # Vérification données
        if not all([nom, prenom, email, telephone, mot_de_passe]):
            flash("Tous les champs sont obligatoires.", "warning")
            return render_template("register.html")

        # Vérifier si l'utilisateur existe déjà
        utilisateur_existe = Utilisateur.query.filter(
            (Utilisateur.email == email) | (Utilisateur.telephone == telephone)
        ).first()

        if utilisateur_existe:
            flash("Cet email ou numéro de téléphone est déjà utilisé.", "warning")
            return render_template("register.html")

        try:
            hash_mdp = generate_password_hash(mot_de_passe)

            nouvel_utilisateur = Utilisateur(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                mot_de_passe=hash_mdp
            )

            db.session.add(nouvel_utilisateur)
            db.session.commit()

            flash("Inscription réussie ! Connecte-toi maintenant 👍", "success")
            return redirect(url_for('auth.connexion'))

        except Exception as e:
            db.session.rollback()
            print("Erreur SQL → ", e)  # log dans Render ou terminal local
            flash("Erreur interne. Réessaie.", "danger")

    return render_template("register.html")



# ============================
# 🔹2 CONNEXION
# ============================
@auth.route('/connexion', methods=['GET', 'POST'])
@limiter.limit("5 per 15 minutes")
def connexion():
    if request.method == 'POST':
        email = request.form.get('email')
        mot_de_passe = request.form.get('mot_de_passe')

        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if utilisateur and check_password_hash(utilisateur.mot_de_passe, mot_de_passe):
            session.clear()
            session.modified = True
            session.permanent = True

            session['user_id'] = utilisateur.id
            session['user_nom'] = utilisateur.nom
            session['is_admin'] = bool(utilisateur.is_admin)

            flash("Connexion réussie ✅", "success")
            return redirect(url_for('main.accueil'))

        flash("Email ou mot de passe incorrect.", "danger")
        return redirect(url_for('auth.connexion'))

    return render_template('login.html')


# ============================
# 🔹3 DÉCONNEXION
# ============================
@auth.route('/deconnexion')
def deconnexion():
    session.clear()
    flash('Déconnexion réussie 👋')
    return redirect(url_for('main.accueil'))


# ============================
# 🔹 4 TABLEAU DE BORD UTILISATEUR
# ============================
@auth.route('/tableau-de-bord')
def tableau_de_bord():
    if 'user_id' not in session:
        flash("Veuillez vous connecter d'abord.", "warning")
        return redirect(url_for('auth.connexion'))

    user_id = session['user_id']
    user = Utilisateur.query.get(user_id)

    conversions = (
        Conversion.query
        .filter_by(user_id=user_id)
        .order_by(Conversion.date_conversion.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'dashboard.html',
        user=user,
        conversions=conversions
    )


# ============================
# 🔹5 MODIFIER PROFIL
# ============================
@auth.route('/modifier-profil', methods=['GET', 'POST'])
def modifier_profil():
    if not session.get('user_id'):
        flash("Veuillez vous connecter pour modifier votre profil.", "warning")
        return redirect(url_for('auth.connexion'))

    user_id = session.get('user_id')
    user = Utilisateur.query.get(user_id)

    if request.method == 'POST':
        user.nom = request.form['nom']
        user.prenom = request.form['prenom']
        user.email = request.form['email']
        user.telephone = request.form['telephone']

        nouveau_mdp = request.form.get('mot_de_passe')
        if nouveau_mdp:
            user.mot_de_passe = generate_password_hash(nouveau_mdp)

        db.session.commit()
        flash("Profil mis à jour avec succès ✅")
        session['user_nom'] = user.nom
        return redirect(url_for('auth.tableau_de_bord'))

    return render_template('edit_profile.html', user=user)


# ============================
# 🔹6 MON SOLDE (avec dépôt simulé)
# ============================
@auth.route('/mon-solde', methods=['GET', 'POST'])
def mon_solde():
    if not session.get('user_id'):
        flash("Veuillez vous connecter.", "warning")
        return redirect(url_for('auth.connexion'))

    user = Utilisateur.query.get_or_404(session['user_id'])
    compte = Compte.query.filter_by(user_id=user.id).first()

    if not compte:
        compte = Compte(user_id=user.id, solde=0)
        db.session.add(compte)
        db.session.commit()

    if request.method == 'POST':
        try:
            montant = float(request.form.get('montant', 0))
            if montant <= 0:
                raise ValueError

            compte.solde += montant
            transaction = Transaction(
                user_id=user.id,
                type="depot",
                montant=montant,
                fournisseur="Simulation",
                reference=str(uuid.uuid4())[:12],
                statut="valide",
                date_transaction=datetime.utcnow()
            )
            db.session.add(transaction)
            db.session.commit()

            flash(f"Dépôt de {montant:.0f} FCFA ajouté ✅", "success")
        except ValueError:
            flash("Montant invalide.", "danger")

        return redirect(url_for('auth.mon_solde'))

    transactions = Transaction.query.filter_by(user_id=user.id).all()
    return render_template("mon_solde.html", user=user, compte=compte, transactions=transactions)



# ============================
# 🔹7 MOT DE PASSE OUBLIÉ (simple, sans email)
# ============================
@auth.route('/mot-de-passe-oublie', methods=['GET', 'POST'])
@limiter.limit("3 per hour")
def mot_de_passe_oublie():
    if request.method == 'POST':
        email = request.form.get('email')

        user = Utilisateur.query.filter_by(email=email).first()

        # ⚠️ Anti-enumération
        if not user:
            flash("Si le compte existe, un lien sera généré.", "info")
            return redirect(url_for('auth.mot_de_passe_oublie'))

        token = user.generate_reset_token(expires_sec=900)
        reset = ResetToken(
                     user_id=user.id,
                     token=token,
                     expire_at=datetime.utcnow() + timedelta(minutes=15)
                )
        db.session.add(reset)
        db.session.commit()


        # TEMPORAIRE (sans email)
        flash(f"Lien temporaire : /reset/{token}", "warning")

        return redirect(url_for('auth.connexion'))

    return render_template("forgot_password.html")




@auth.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    reset = ResetToken.query.filter_by(token=token, used=False).first()

    if not reset or not reset.is_valid():
        flash("Lien invalide ou expiré.", "danger")
        return redirect(url_for('auth.connexion'))

    if request.method == 'POST':
        mdp = request.form.get('mot_de_passe')
        confirm = request.form.get('confirmation')

        if not mdp or mdp != confirm:
            flash("Les mots de passe ne correspondent pas.", "warning")
            return render_template("reset_password.html")

        user = Utilisateur.query.get_or_404(reset.user_id)
        user.mot_de_passe = generate_password_hash(mdp)

        reset.used = True
        db.session.commit()

        flash("Mot de passe réinitialisé avec succès ✅", "success")
        return redirect(url_for('auth.connexion'))

    return render_template("reset_password.html")


