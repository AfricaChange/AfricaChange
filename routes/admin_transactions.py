#DEPENDANCES
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from database import db
from models import Transaction, Paiement, Conversion, Utilisateur
from services.admin_actions import AdminActions
from services.risk_engine import RiskEngine







admin_tx = Blueprint(
    "admin_tx",
    __name__,
    url_prefix="/admin/transactions"
)


#SECURITE ADMIN
@admin_tx.before_request
def admin_only():
    if not session.get("is_admin"):
        abort(403)


#LISTE DES TRANSACTIONS(VU GLOBALE)
@admin_tx.route("/")
def liste():
    transactions = (
        Transaction.query
        .order_by(Transaction.date_transaction.desc())
        .limit(200)
        .all()
    )

    return render_template(
        "admin/transactions_list.html",
        transactions=transactions
    )

@admin_tx.route("/<reference>")
def detail(reference):
    tx = Transaction.query.filter_by(reference=reference).first_or_404()

    paiement = Paiement.query.filter_by(
        transaction_reference=tx.reference
    ).first()

    conversion = Conversion.query.get(tx.user_id)

    risk_score = RiskEngine.score_transaction(tx, request.remote_addr)

    return render_template(
        "admin/transaction_detail.html",
        transaction=tx,
        paiement=paiement,
        conversion=conversion,
        risk_score=risk_score
    )


@admin_tx.route("/<reference>/validate", methods=["POST"])
def validate(reference):
    tx = Transaction.query.filter_by(reference=reference).first_or_404()

    try:
        AdminActions.action_validate(
            tx=tx,
            admin_id=session.get("user_id"),
            ip=request.remote_addr
        )
        db.session.commit()
        flash("Transaction validée avec succès ✅", "success")

    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")

    return redirect(url_for("admin_tx.detail", reference=reference))


@admin_tx.route("/<reference>/block", methods=["POST"])
def block(reference):
    reason = request.form.get("reason", "").strip()
    tx = Transaction.query.filter_by(reference=reference).first_or_404()

    if not reason:
        flash("Motif obligatoire", "warning")
        return redirect(url_for("admin_tx.detail", reference=reference))

    try:
        AdminActions.block(
            tx=tx,
            admin_id=session.get("user_id"),
            ip=request.remote_addr,
            reason=reason
        )
        db.session.commit()
        flash("Transaction bloquée ⛔", "warning")

    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")

    return redirect(url_for("admin_tx.detail", reference=reference))



@admin_tx.route("/<reference>/refund", methods=["POST"])
def refund(reference):
    reason = request.form.get("reason", "").strip()
    tx = Transaction.query.filter_by(reference=reference).first_or_404()

    if not reason:
        flash("Motif obligatoire", "warning")
        return redirect(url_for("admin_tx.detail", reference=reference))

    try:
        AdminActions.refund(
            tx=tx,
            admin_id=session.get("user_id"),
            ip=request.remote_addr,
            reason=reason
        )
        db.session.commit()
        flash("Remboursement effectué 🔁", "success")

    except Exception as e:
        db.session.rollback()
        flash(str(e), "danger")

    return redirect(url_for("admin_tx.detail", reference=reference))
