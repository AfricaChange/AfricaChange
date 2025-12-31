from flask import Blueprint, request, jsonify, session
from models import Transaction
from services.admin_actions import AdminActions

admin_actions_bp = Blueprint("admin_actions", __name__, url_prefix="/admin/actions")

@admin_actions_bp.route("/validate", methods=["POST"])
def validate_tx():
    data = request.get_json()
    tx = Transaction.query.filter_by(reference=data["reference"]).first_or_404()

    AdminActions.validate(
        tx=tx,
        admin_id=session.get("user_id"),
        ip=request.remote_addr,
        reason=data.get("reason")
    )

    db.session.commit()
    return jsonify(success=True)


@admin_actions_bp.route("/block", methods=["POST"])
def block_tx():
    data = request.get_json()
    tx = Transaction.query.filter_by(reference=data["reference"]).first_or_404()

    AdminActions.block(
        tx=tx,
        admin_id=session.get("user_id"),
        ip=request.remote_addr,
        reason=data["reason"]
    )

    db.session.commit()
    return jsonify(success=True)


@admin_actions_bp.route("/refund", methods=["POST"])
def refund_tx():
    data = request.get_json()
    tx = Transaction.query.filter_by(reference=data["reference"]).first_or_404()

    AdminActions.refund(
        tx=tx,
        admin_id=session.get("user_id"),
        ip=request.remote_addr,
        amount=float(data["amount"]),
        reason=data["reason"]
    )

    db.session.commit()
    return jsonify(success=True)
