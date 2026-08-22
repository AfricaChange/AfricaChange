from datetime import datetime
import random
import string

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import or_

from database import db
from extensions import csrf
from models import Conversion, Rate
from services.constants import PaymentStatus
from services.homepage_quote_service import build_quote
from services.liquidity_service import LiquidityService


convert = Blueprint("convert", __name__, url_prefix="/convert")

MAX_PUBLIC_AMOUNT = 500000  # 500 000 CFA max pour non connectes


@convert.route("/", methods=["GET", "POST"])
def convertir():
    if request.method == "POST":
        try:
            montant = float(request.form.get("montant", 0))
            user_id = session.get("user_id")

            if not user_id and montant > MAX_PUBLIC_AMOUNT:
                flash(
                    f"Pour convertir plus de {MAX_PUBLIC_AMOUNT:,} CFA, veuillez vous connecter.",
                    "warning",
                )
                return redirect(url_for("auth.connexion"))

        except ValueError:
            flash("Montant invalide.", "error")
            return redirect(url_for("convert.convertir"))

        if montant <= 0:
            flash("Le montant doit etre superieur a 0.", "warning")
            return redirect(url_for("convert.convertir"))

        from_currency = request.form.get("from_currency")
        to_currency = request.form.get("to_currency")
        sender_phone = request.form.get("sender_phone")
        receiver_phone = request.form.get("receiver_phone")

        if not all([from_currency, to_currency, sender_phone, receiver_phone]):
            flash("Tous les champs sont obligatoires.", "warning")
            return redirect(url_for("convert.convertir"))

        rate = Rate.query.filter_by(
            from_currency=from_currency,
            to_currency=to_currency,
        ).first()

        if not rate:
            flash("Taux non defini pour cette paire de devises.", "error")
            return redirect(url_for("convert.convertir"))

        montant_converti = round(montant * rate.rate, 2)
        reference = "CVT-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

        nouvelle_conversion = Conversion(
            user_id=session.get("user_id"),
            from_currency=from_currency,
            to_currency=to_currency,
            montant_initial=montant,
            montant_converti=montant_converti,
            sender_phone=sender_phone,
            receiver_phone=receiver_phone,
            reference=reference,
            statut=PaymentStatus.EN_ATTENTE.value,
            date_conversion=datetime.utcnow(),
        )

        db.session.add(nouvelle_conversion)
        db.session.commit()

        flash(f"Conversion reussie. Reference : {reference}", "success")
        return redirect(url_for("convert.recap", reference=reference))

    initial_form = {
        "montant": request.args.get("montant", ""),
        "from_currency": request.args.get("from_currency", "CFA"),
        "to_currency": request.args.get("to_currency", "GNF"),
        "sender_phone": request.args.get("sender_phone", ""),
        "receiver_phone": request.args.get("receiver_phone", ""),
    }

    return render_template("convert.html", initial_form=initial_form)


@csrf.exempt
@convert.route("/api/convertir", methods=["POST"])
def api_convertir():
    data = request.get_json(silent=True) or {}

    try:
        montant = float(data.get("montant", 0))
    except ValueError:
        return jsonify({"error": "Montant invalide"}), 400

    if montant <= 0:
        return jsonify({"error": "Montant invalide"}), 400

    quote = build_quote(
        amount=montant,
        from_currency=data.get("from_currency"),
        to_currency=data.get("to_currency"),
    )

    if not quote["ok"]:
        return jsonify({"error": quote["error_message"]}), 400

    return jsonify(
        {
            "taux": quote["rate"],
            "montant_converti": quote["amount_received"],
            "frais_connus": quote["fee_known"],
            "frais_label": quote["fee_label"],
            "corridor": quote["corridor_key"],
            "from_currency": quote["from_currency"],
            "to_currency": quote["to_currency"],
            "from_country_code": quote["from_country_code"],
            "from_country_name": quote["from_country_name"],
            "from_flag": quote["from_flag"],
            "to_country_code": quote["to_country_code"],
            "to_country_name": quote["to_country_name"],
            "to_flag": quote["to_flag"],
        }
    )


@convert.route("/confirmer/<reference>", methods=["POST"])
def confirmer_envoi_par_reference(reference):
    conversion = Conversion.query.filter_by(reference=reference).first()

    if not conversion:
        return jsonify({"error": "Conversion introuvable"}), 404

    if conversion.statut != PaymentStatus.EN_ATTENTE.value:
        return jsonify({"error": "Conversion deja traitee."}), 400

    try:
        LiquidityService.assign_for_conversion(conversion)
        conversion.statut = PaymentStatus.EN_COURS.value
        db.session.commit()

        actor = conversion.merchant.nom if conversion.merchant else conversion.compte_systeme.nom
        return jsonify(
            {
                "message": f"Paiement en cours via {actor}",
                "liquidity_source": conversion.liquidity_source_type,
                "reference": conversion.reference,
            }
        ), 200

    except Exception:
        conversion.statut = PaymentStatus.ECHOUE.value
        db.session.commit()
        return jsonify({"error": "Erreur lors du traitement"}), 500


@convert.route("/historique")
def historique():
    if not session.get("user_id"):
        flash("Veuillez vous connecter.", "warning")
        return redirect(url_for("auth.connexion"))

    user_id = session["user_id"]
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    per_page = 10

    query = Conversion.query.filter(
        Conversion.user_id == user_id,
        Conversion.statut.in_(
            [
                PaymentStatus.EN_ATTENTE.value,
                "paiement_en_cours",
                PaymentStatus.VALIDE.value,
                PaymentStatus.ECHOUE.value,
            ]
        ),
    )

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Conversion.reference.like(like),
                Conversion.from_currency.like(like),
                Conversion.to_currency.like(like),
                Conversion.sender_phone.like(like),
                Conversion.receiver_phone.like(like),
            )
        )

    pagination = query.order_by(Conversion.date_conversion.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False,
    )

    return render_template(
        "historique.html",
        conversions=pagination.items,
        pagination=pagination,
        search=search,
    )


@convert.route("/recap/<reference>")
def recap(reference):
    conversion = Conversion.query.filter_by(reference=reference).first()

    if not conversion:
        flash("Conversion introuvable.", "danger")
        return redirect(url_for("convert.convertir"))

    if conversion.user_id and conversion.user_id != session.get("user_id"):
        flash("Acces non autorise.", "danger")
        return redirect(url_for("main.accueil"))

    return render_template("recap.html", conversion=conversion)
