from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database import db
from models import Utilisateur, Compte, Transaction, Conversion
from datetime import datetime
import uuid

auth = Blueprint('auth', __name__)

# ============================
# 🔹1 INSCRIPTION
# ============================
@auth.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form['telephone']
        mot_de_passe = generate_password_hash(request.form['mot_de_passe'])

        # Vérifier si l'utilisateur existe déjà
        utilisateur_existe = Utilisateur.query.filter(
            (Utilisateur.email == email) | (Utilisateur.telephone == telephone)
        ).first()

        if utilisateur_existe:
            flash("Cet email ou numéro de téléphone est déjà utilisé.", "warning")
            return redirect(url_for('auth.inscription'))

        nouvel_utilisateur = Utilisateur(
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            mot_de_passe=mot_de_passe
        )
        db.session.add(nouvel_utilisateur)
        db.session.commit()

        flash("Inscription réussie ✅ Connecte-toi maintenant.", "success")
        return redirect(url_for('auth.connexion'))

    return render_template('register.html')


# ============================
# 🔹2 CONNEXION
# ============================
@auth.route('/connexion', methods=['GET', 'POST'])
def connexion():
    if request.method == 'POST':
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']

        utilisateur = Utilisateur.query.filter_by(email=email).first()

        if utilisateur and check_password_hash(utilisateur.mot_de_passe, mot_de_passe):
            session['user_id'] = utilisateur.id
            session['user_nom'] = utilisateur.nom
            session['is_admin'] = bool(utilisateur.is_admin)

            flash('Connexion réussie ✅')
            return redirect(url_for('main.accueil'))
        else:
            flash("Email ou mot de passe incorrect.", "error")
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
    user_id = session.get('user_id')
    if not user_id:
        flash("Veuillez vous connecter pour accéder à cette page.", "warning")
        return redirect(url_for('auth.connexion'))

    # Récupération de l’utilisateur et de son compte
    user = Utilisateur.query.get(user_id)
    compte = Compte.query.filter_by(user_id=user_id).first()

    if not compte:
        compte = Compte(user_id=user_id, solde=0)
        db.session.add(compte)
        db.session.commit()

    # Si l’utilisateur simule un dépôt
    if request.method == 'POST':
        try:
            montant = float(request.form['montant'])
            if montant <= 0:
                flash("Le montant doit être supérieur à 0.", "warning")
                return redirect(url_for('auth.mon_solde'))

            compte.solde += montant
            transaction = Transaction(
                user_id=user.id,
                type='depot',
                montant=montant,
                fournisseur="Simulation",
                reference=str(uuid.uuid4())[:10],
                statut='valide',
                date_transaction=datetime.utcnow()
            )
            db.session.add(transaction)
            db.session.commit()

            flash(f"Dépôt de {montant:.0f} FCFA ajouté avec succès ✅")
        except ValueError:
            flash("Montant invalide.", "error")

        return redirect(url_for('auth.mon_solde'))

    # Liste des transactions
    transactions = (
        Transaction.query
        .filter_by(user_id=user_id)
        .order_by(Transaction.date_transaction.desc())
        .all()
    )

    return render_template('mon_solde.html', user=user, compte=compte, transactions=transactions)


# ============================
# 🔹7 MOT DE PASSE OUBLIÉ (simple, sans email)
# ============================
@auth.route('/mot-de-passe-oublie', methods=['GET', 'POST'])
def mot_de_passe_oublie():
    if request.method == 'POST':
        email = request.form.get('email')
        nouveau = request.form.get('nouveau_mot_de_passe')
        confirmation = request.form.get('confirmation_mot_de_passe')

        if not email or not nouveau or not confirmation:
            flash("Veuillez remplir tous les champs.", "error")
            return render_template("forgot_password.html", email=email)

        if nouveau != confirmation:
            flash("Les mots de passe ne correspondent pas.", "error")
            return render_template("forgot_password.html", email=email)

        # Chercher l'utilisateur
        user = Utilisateur.query.filter_by(email=email).first()
        if not user:
            flash("Aucun compte trouvé avec cet email.", "error")
            return render_template("forgot_password.html", email=email)

        # Mettre à jour le mot de passe (haché)
        user.mot_de_passe = generate_password_hash(nouveau)
        db.session.commit()

        flash("✅ Mot de passe réinitialisé. Vous pouvez vous connecter.", "success")
        return redirect(url_for('auth.connexion'))

    # GET : afficher le formulaire
    return render_template("forgot_password.html")
