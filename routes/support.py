from flask import Blueprint, render_template, request, flash, redirect, url_for

support = Blueprint("support", __name__)

@support.route("/support", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nom = request.form.get("nom")
        email = request.form.get("email")
        sujet = request.form.get("sujet")
        message = request.form.get("message")

        if not nom or not email or not message:
            flash("Veuillez remplir tous les champs obligatoires.", "error")
            return redirect(url_for("support.index"))

        # 👉 Pour l’instant on log, plus tard email / ticket
        print("📩 MESSAGE SUPPORT")
        print(nom, email, sujet, message)

        flash("Votre message a bien été envoyé. Nous vous répondrons rapidement.", "success")
        return redirect(url_for("support.index"))

    return render_template("support.html")
