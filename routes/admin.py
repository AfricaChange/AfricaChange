from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, session, send_file
from database import db
from models import (
    AuditLog,
    Compte,
    CompteSysteme,
    Conversion,
    Currency,
    Dispute,
    Merchant,
    MerchantRate,
    Parametre,
    Rate,
    RiskEvent,
    Settlement,
    Transaction,
    Utilisateur,
    WalletEntry,
    AdminWalletAction,
)
import io
from datetime import datetime
from openpyxl import Workbook
from io import BytesIO 
from functools import wraps
from services.liquidity_service import LiquidityService
from services.dispute_service import DisputeService
from services.settlement_service import SettlementService
from services.payment_mode_service import PaymentModeService
from services.merchant_dashboard_service import MerchantDashboardService
from services.merchant_wallet_admin_service import MerchantWalletAdminService
from services.senepay_sandbox_test_service import SenePaySandboxTestService
from services.wallet_service import WalletService
 










admin = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id') or not session.get('is_admin'):
            flash("Accès refusé.", "danger")
            return redirect(url_for('main.accueil'))
        return f(*args, **kwargs)
    return decorated


# ============================
# 1️⃣ Tableau de bord principal
# ============================


@admin.route('/dashboard')
@admin_required
def dashboard():
    total_users = Utilisateur.query.count()
    total_transactions = Transaction.query.count()
    total_fonds = db.session.query(db.func.sum(Compte.solde)).scalar() or 0.0
    transactions = Transaction.query.order_by(Transaction.date_transaction.desc()).limit(5).all()

    # 👉 Récupération des taux actuels
    taux_list = Rate.query.all()
    
    # 🔴 TRANSACTIONS
    tx_pending = Transaction.query.filter_by(statut="en_attente").count()
    tx_valid = Transaction.query.filter_by(statut="valide").count()
    tx_blocked = Transaction.query.filter_by(statut="bloque").count()
    tx_failed = Transaction.query.filter_by(statut="echoue").count()

    # 🔵 CONVERSIONS (avant paiement)
    conv_pending = Conversion.query.filter_by(statut="en_attente").count()

    total_transactions = Transaction.query.count()
    total_fonds = db.session.query(db.func.sum(Compte.solde)).scalar() or 0.0

    # dernières transactions
    transactions = (
        Transaction.query
        .order_by(Transaction.date_transaction.desc())
        .limit(10)
        .all()
    )

    taux_list = Rate.query.all()

    return render_template(
        "admin_dashboard.html",
        total_users=total_users,
        total_transactions=total_transactions,
        total_fonds=total_fonds,
        transactions=transactions,
        taux_list=taux_list,

        # 👇 STATS TEMPS RÉEL
        tx_pending=tx_pending,
        tx_valid=tx_valid,
        tx_blocked=tx_blocked,
        tx_failed=tx_failed,
        conv_pending=conv_pending
    )

   

   

# ============================
# 2️⃣ Gestion des taux
# ============================

@admin.route('/taux', methods=['GET', 'POST'])
@admin_required
def gerer_taux():
    

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
@admin.route('/conversions')
@admin_required
def liste_conversions():
    """Liste des conversions pour l’admin"""
    conversions = (
        Conversion.query
        .order_by(Conversion.date_conversion.desc())
        .all()
    )
    return render_template(
        'admin_conversions.html',
        conversions=conversions
    )
    
# 🔹 Liste filtrable des conversions
@admin.route('/conversions/export')
@admin_required
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
        "Source liquidité",
        "Porteur risque",
        "Compte système",
        "Marchand"
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
            c.liquidity_source_type,
            c.risk_bearer,
            c.compte_systeme.nom if c.compte_systeme else "",
            c.merchant.nom if c.merchant else ""
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
@admin_required
def historique_envois():
    page = request.args.get("page", 1, type=int)
    statut = request.args.get("statut", None)

    query = Conversion.query.order_by(Conversion.date_conversion.desc())

    if statut and statut in ["en_attente", "paiement_en_cours", "valide", "echoue"]:
       query = query.filter(Conversion.statut == statut)


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
@admin_required
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
@admin_required
def toggle_compte(id):
    """Active ou désactive un compte système."""
    compte = CompteSysteme.query.get_or_404(id)
    compte.actif = not compte.actif
    db.session.commit()
    statut = "activé" if compte.actif else "désactivé"
    flash(f"🔄 Compte {compte.nom} {statut}.", "info")
    return redirect(url_for('admin.comptes_systeme'))


@admin.route('/comptes-systeme/supprimer/<int:id>', methods=['POST'])
@admin_required
def supprimer_compte(id):
    """Supprime définitivement un compte système."""
    compte = CompteSysteme.query.get_or_404(id)
    db.session.delete(compte)
    db.session.commit()
    flash(f"🗑️ Compte {compte.nom} supprimé.", "danger")
    return redirect(url_for('admin.comptes_systeme'))


@admin.route('/marchands', methods=['GET', 'POST'])
@admin_required
def marchands():
    if request.method == 'POST':
        action = request.form.get("action", "").strip()

        try:
            if action == "create_merchant":
                code = request.form.get("code", "").strip().upper()
                nom = request.form.get("nom", "").strip()
                telephone = request.form.get("telephone", "").strip()
                email = request.form.get("email", "").strip() or None
                pays = request.form.get("pays", "").strip()
                min_ticket = float(request.form.get("min_ticket", 0) or 0)
                max_ticket_raw = request.form.get("max_ticket", "").strip()
                max_ticket = float(max_ticket_raw) if max_ticket_raw else None
                solde_disponible = float(request.form.get("solde_disponible", 0) or 0)

                if not all([code, nom, telephone, pays]):
                    raise ValueError("Code, nom, telephone et pays sont obligatoires.")
                if min_ticket < 0 or solde_disponible < 0:
                    raise ValueError("Les montants ne peuvent pas etre negatifs.")
                if max_ticket is not None and max_ticket <= 0:
                    raise ValueError("Le ticket maximum doit etre superieur a 0.")
                if max_ticket is not None and max_ticket < min_ticket:
                    raise ValueError("Le ticket maximum doit etre superieur ou egal au minimum.")

                merchant = Merchant(
                    code=code,
                    nom=nom,
                    telephone=telephone,
                    email=email,
                    pays=pays,
                    actif=request.form.get("actif") == "on",
                    verifie=request.form.get("verifie") == "on",
                    risk_score=int(request.form.get("risk_score", 0) or 0),
                    solde_disponible=solde_disponible,
                    min_ticket=min_ticket,
                    max_ticket=max_ticket,
                )
                db.session.add(merchant)
                db.session.commit()
                flash(f"Marchand {merchant.nom} ajoute avec succes.", "success")
                return redirect(url_for('admin.marchands'))

            if action == "create_rate":
                merchant_id = int(request.form.get("merchant_id", 0) or 0)
                from_currency = request.form.get("from_currency", "").strip().upper()
                to_currency = request.form.get("to_currency", "").strip().upper()
                rate_value = float(request.form.get("rate", 0) or 0)

                if not merchant_id or not all([from_currency, to_currency]):
                    raise ValueError("Marchand et paire de devises obligatoires.")
                if rate_value <= 0:
                    raise ValueError("Le taux marchand doit etre superieur a 0.")

                merchant = Merchant.query.get_or_404(merchant_id)
                existing = MerchantRate.query.filter_by(
                    merchant_id=merchant.id,
                    from_currency=from_currency,
                    to_currency=to_currency,
                ).first()

                if existing:
                    existing.rate = rate_value
                    existing.actif = request.form.get("actif_rate") == "on"
                    flash(f"Taux mis a jour pour {merchant.nom}.", "success")
                else:
                    merchant_rate = MerchantRate(
                        merchant_id=merchant.id,
                        from_currency=from_currency,
                        to_currency=to_currency,
                        rate=rate_value,
                        actif=request.form.get("actif_rate") == "on",
                    )
                    db.session.add(merchant_rate)
                    flash(f"Taux ajoute pour {merchant.nom}.", "success")

                db.session.commit()
                return redirect(url_for('admin.marchands'))

            raise ValueError("Action admin invalide.")

        except Exception as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            return redirect(url_for('admin.marchands'))

    merchants = Merchant.query.order_by(Merchant.created_at.desc()).all()
    merchant_rates = MerchantRate.query.order_by(
        MerchantRate.merchant_id.asc(),
        MerchantRate.from_currency.asc(),
        MerchantRate.to_currency.asc(),
    ).all()
    return render_template(
        'admin_merchants.html',
        merchants=merchants,
        merchant_rates=merchant_rates,
    )


@admin.route('/marchands/<int:id>/dashboard')
@admin_required
def merchant_dashboard(id):
    merchant = Merchant.query.get_or_404(id)
    snapshot = MerchantDashboardService.snapshot(merchant)
    return render_template(
        'admin_merchant_dashboard.html',
        snapshot=snapshot,
        merchant=merchant,
    )


@admin.route('/marchands/<int:id>/wallet', methods=['GET', 'POST'])
@admin_required
def merchant_wallet(id):
    merchant = Merchant.query.get_or_404(id)

    if request.method == 'POST':
        action = request.form.get("action", "").strip().lower()
        currency = request.form.get("currency", "").strip().upper()
        reason = request.form.get("reason", "").strip()
        reference = request.form.get("reference", "").strip() or None
        high_amount_confirmed = request.form.get("confirm_high_amount") == "on"

        try:
            amount = float(request.form.get("amount", 0) or 0)
        except (TypeError, ValueError):
            amount = 0

        try:
            if amount <= 0:
                raise ValueError("Le montant doit etre superieur a 0.")

            result = MerchantWalletAdminService.execute(
                merchant=merchant,
                action=action,
                currency=currency,
                amount=amount,
                admin_user_id=session.get("user_id"),
                ip_address=request.remote_addr or "unknown",
                reason=reason,
                reference=reference,
                session_identifier=request.cookies.get("session"),
                high_amount_confirmed=high_amount_confirmed,
            )
            db.session.commit()
            flash(
                f"Operation wallet {action} appliquee sur {merchant.nom} ({currency}) - ref {result['reference']}.",
                "success",
            )
            return redirect(url_for('admin.merchant_wallet', id=merchant.id))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), "danger")
            return redirect(url_for('admin.merchant_wallet', id=merchant.id))

    currencies = Currency.query.filter_by(is_active=True).order_by(Currency.code.asc()).all()
    balances = WalletService.balances_for_merchant(merchant)
    entries = (
        WalletEntry.query
        .filter_by(merchant_id=merchant.id)
        .order_by(WalletEntry.created_at.desc(), WalletEntry.id.desc())
        .limit(20)
        .all()
    )
    admin_actions = (
        AdminWalletAction.query
        .filter_by(merchant_id=merchant.id)
        .order_by(AdminWalletAction.created_at.desc(), AdminWalletAction.id.desc())
        .limit(20)
        .all()
    )
    return render_template(
        'admin_merchant_wallet.html',
        merchant=merchant,
        balances=balances,
        currencies=currencies,
        entries=entries,
        admin_actions=admin_actions,
    )


@admin.route('/marchands/toggle/<int:id>', methods=['POST'])
@admin_required
def toggle_marchand(id):
    merchant = Merchant.query.get_or_404(id)
    merchant.actif = not merchant.actif
    db.session.commit()
    flash(f"Marchand {merchant.nom} {'active' if merchant.actif else 'desactive'}.", "info")
    return redirect(url_for('admin.marchands'))


@admin.route('/marchands/verify/<int:id>', methods=['POST'])
@admin_required
def verify_marchand(id):
    merchant = Merchant.query.get_or_404(id)
    merchant.verifie = not merchant.verifie
    db.session.commit()
    flash(f"Verification de {merchant.nom} mise a jour.", "info")
    return redirect(url_for('admin.marchands'))


@admin.route('/marchands/supprimer/<int:id>', methods=['POST'])
@admin_required
def supprimer_marchand(id):
    merchant = Merchant.query.get_or_404(id)
    has_active_conversions = Conversion.query.filter_by(
        merchant_id=merchant.id,
    ).filter(
        Conversion.statut.in_(["en_attente", "paiement_en_cours"])
    ).first()

    if has_active_conversions:
        flash("Suppression refusee: ce marchand a des conversions en cours.", "warning")
        return redirect(url_for('admin.marchands'))

    MerchantRate.query.filter_by(merchant_id=merchant.id).delete()
    db.session.delete(merchant)
    db.session.commit()
    flash(f"Marchand {merchant.nom} supprime.", "danger")
    return redirect(url_for('admin.marchands'))


@admin.route('/marchands/rates/toggle/<int:id>', methods=['POST'])
@admin_required
def toggle_taux_marchand(id):
    merchant_rate = MerchantRate.query.get_or_404(id)
    merchant_rate.actif = not merchant_rate.actif
    db.session.commit()
    flash("Taux marchand mis a jour.", "info")
    return redirect(url_for('admin.marchands'))


@admin.route('/reglements')
@admin_required
def reglements():
    status = request.args.get("status", "").strip()
    query = Settlement.query.order_by(Settlement.created_at.desc())

    if status in {"pending", "completed"}:
        query = query.filter_by(status=status)

    settlements = query.all()
    pending_count = Settlement.query.filter_by(status="pending").count()
    completed_count = Settlement.query.filter_by(status="completed").count()
    return render_template(
        "admin_settlements.html",
        settlements=settlements,
        selected_status=status,
        pending_count=pending_count,
        completed_count=completed_count,
    )


@admin.route('/reglements/<int:id>/complete', methods=['POST'])
@admin_required
def complete_reglement(id):
    settlement = Settlement.query.get_or_404(id)
    notes = request.form.get("notes", "").strip() or None

    try:
        SettlementService.complete_settlement(
            settlement=settlement,
            admin_id=session.get("user_id"),
            ip=request.remote_addr,
            notes=notes,
        )
        db.session.commit()
        flash(f"Reglement {settlement.reference} cloture.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(url_for('admin.reglements'))


@admin.route('/conversions/release-expired', methods=['POST'])
@admin_required
def release_expired_conversions():
    expired = LiquidityService.expire_stale_reservations()
    if expired:
        db.session.commit()
        flash(f"{len(expired)} reservation(s) expiree(s) liberee(s).", "success")
    else:
        db.session.rollback()
        flash("Aucune reservation expiree a liberer.", "info")
    return redirect(url_for('admin.liste_conversions'))


@admin.route('/conversions/<reference>/force-release', methods=['POST'])
@admin_required
def force_release_conversion(reference):
    conversion = Conversion.query.filter_by(reference=reference).first_or_404()

    if conversion.liquidity_source_type != "merchant":
        flash("Cette conversion n'utilise pas la liquidite marchand.", "warning")
        return redirect(url_for('admin.liste_conversions'))

    try:
        released = LiquidityService.release_expired_reservation(
            conversion,
            reason="admin_force_release",
        )
        if not released:
            raise ValueError("Aucune reservation active a liberer.")

        db.session.add(
            AuditLog(
                actor_type="admin",
                actor_id=session.get("user_id"),
                event="merchant_reservation_force_released",
                payload={"reference": conversion.reference},
                ip_address=request.remote_addr,
            )
        )
        db.session.commit()
        flash(f"Reservation de {reference} liberee.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(url_for('admin.liste_conversions'))





# ===============================================================
# 🏦 ROUTE DE MAINTENANCE
# ===============================================================
@admin.route("/maintenance", methods=["GET", "POST"])
@admin_required
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


@admin.route("/payment-mode", methods=["GET", "POST"])
@admin_required
def payment_mode():
    if request.method == "POST":
        selected_mode = request.form.get("payment_mode", "").strip().lower()

        try:
            PaymentModeService.set_mode(selected_mode)
            db.session.commit()
            flash("Mode de paiement global mis a jour.", "success")
            return redirect(url_for("admin.payment_mode"))
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    current_mode = PaymentModeService.get_mode()
    return render_template(
        "admin_payment_mode.html",
        current_mode=current_mode,
        allowed_modes=sorted(PaymentModeService.ALLOWED_MODES),
    )


@admin.route("/senepay-sandbox", methods=["GET", "POST"])
@admin_required
def senepay_sandbox():
    result = None

    if request.method == "POST":
        action = request.form.get("action", "").strip()
        payload = {
            "internal_reference": request.form.get("internal_reference", "").strip() or None,
            "amount": request.form.get("amount", "").strip() or None,
            "currency": request.form.get("currency", "").strip().upper() or None,
            "description": request.form.get("description", "").strip() or None,
            "return_url": request.form.get("return_url", "").strip() or None,
            "cancel_url": request.form.get("cancel_url", "").strip() or None,
            "customer_name": request.form.get("customer_name", "").strip() or None,
            "customer_email": request.form.get("customer_email", "").strip() or None,
            "customer_phone": request.form.get("customer_phone", "").strip() or None,
            "phone_number": request.form.get("phone_number", "").strip() or None,
            "operator": request.form.get("operator", "").strip() or None,
            "country": request.form.get("country", "").strip().upper() or None,
            "session_token": request.form.get("session_token", "").strip() or None,
            "token": request.form.get("token", "").strip() or None,
            "beneficiary_name": request.form.get("beneficiary_name", "").strip() or None,
            "beneficiary_phone": request.form.get("beneficiary_phone", "").strip() or None,
            "beneficiary_country": request.form.get("beneficiary_country", "").strip() or None,
            "beneficiary_currency": request.form.get("beneficiary_currency", "").strip().upper() or None,
            "callback_url": request.form.get("callback_url", "").strip() or None,
            "payout_id": request.form.get("payout_id", "").strip() or None,
        }

        try:
            result = SenePaySandboxTestService.execute_action(
                action=action,
                payload=payload,
                admin_user_id=session.get("user_id"),
                ip_address=request.remote_addr or "unknown",
            )
            db.session.commit()
            flash(f"Test Sandbox SenePay execute: {action}.", "success")
        except Exception as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    logs = SenePaySandboxTestService.recent_logs()
    return render_template(
        "admin_senepay_sandbox.html",
        result=result,
        logs=logs,
        senepay_mode=current_app.config.get("SENEPAY_MODE", "sandbox"),
        senepay_base_url=current_app.config.get("SENEPAY_BASE_URL", ""),
    )
    
    
    
@admin.route("/transactions")
@admin_required
def transactions():
    status = request.args.get("status")
    provider = request.args.get("provider")
    search = request.args.get("q")

    query = Transaction.query

    # ✅ Statuts autorisés uniquement
    allowed_statuses = [
        "en_attente",
        "valide",
        "echoue",
        "bloque",
        "rembourse"
    ]

    if status in allowed_statuses:
        query = query.filter(Transaction.statut == status)

    if provider:
        query = query.filter(Transaction.fournisseur == provider)

    if search:
        like = f"%{search}%"
        query = query.filter(Transaction.reference.ilike(like))

    transactions = (
        query
        .order_by(Transaction.date_transaction.desc())
        .limit(100)
        .all()
    )

    return render_template(
        "admin/transactions.html",
        transactions=transactions,
        current_status=status
    )




@admin.route("/risques")
@admin_required
def risques():
    risks = (
        RiskEvent.query
        .order_by(RiskEvent.created_at.desc())
        .limit(100)
        .all()
    )

    return render_template(
        "admin/risques.html",
        risks=risks
    )

    
@admin.route("/utilisateurs")
@admin_required
def utilisateurs():
    users = Utilisateur.query.order_by(Utilisateur.id.desc()).all()

    return render_template(
        "admin/utilisateurs.html",
        users=users
    )

    



@admin.route("/audits")
@admin_required
def audits():
    logs = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .limit(100)
        .all()
    )

    return render_template(
        "admin/audits.html",
        logs=logs
    )


@admin.route("/litiges")
@admin_required
def litiges():
    status = request.args.get("status", "").strip()
    query = Dispute.query.order_by(Dispute.created_at.desc())
    if status in {"open", "resolved"}:
        query = query.filter_by(status=status)

    disputes = query.limit(200).all()
    return render_template(
        "admin_disputes.html",
        disputes=disputes,
        current_status=status,
    )


@admin.route("/litiges/<int:id>/resolve", methods=["POST"])
@admin_required
def resolve_litige(id):
    dispute = Dispute.query.get_or_404(id)
    note = request.form.get("note", "").strip() or None

    try:
        DisputeService.resolve_dispute(
            dispute=dispute,
            admin_id=session.get("user_id"),
            ip=request.remote_addr,
            resolution_note=note,
        )
        db.session.commit()
        flash(f"Litige {dispute.reference} resolu.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(url_for("admin.litiges"))


@admin.route("/marchands/<int:id>/suspend", methods=["POST"])
@admin_required
def suspend_marchand(id):
    merchant = Merchant.query.get_or_404(id)
    reason = request.form.get("reason", "").strip() or "admin_suspension"

    try:
        DisputeService.suspend_merchant(
            merchant=merchant,
            admin_id=session.get("user_id"),
            ip=request.remote_addr,
            reason=reason,
        )
        db.session.commit()
        flash(f"Marchand {merchant.nom} suspendu.", "warning")
    except Exception as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(request.referrer or url_for("admin.marchands"))


@admin.route("/marchands/<int:id>/reinstate", methods=["POST"])
@admin_required
def reinstate_marchand(id):
    merchant = Merchant.query.get_or_404(id)
    reason = request.form.get("reason", "").strip() or None

    try:
        DisputeService.reinstate_merchant(
            merchant=merchant,
            admin_id=session.get("user_id"),
            ip=request.remote_addr,
            reason=reason,
        )
        db.session.commit()
        flash(f"Marchand {merchant.nom} reactive.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(request.referrer or url_for("admin.marchands"))

    
