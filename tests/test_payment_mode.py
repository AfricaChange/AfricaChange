import unittest

from flask import Flask

from database import db
from models import CompteSysteme, Conversion, Parametre, Utilisateur
from routes.paiement import paiement
from services.payment_mode_service import PaymentModeService


class PaymentModeTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SECRET_KEY="test-secret",
            SERVER_NAME="localhost",
        )
        db.init_app(self.app)
        self.app.register_blueprint(paiement)

        @self.app.route("/dashboard")
        def fake_dashboard():
            return "dashboard"

        self.app.add_url_rule("/dashboard", endpoint="auth.tableau_de_bord", view_func=fake_dashboard)
        self.app.add_url_rule("/recap/<reference>", endpoint="convert.recap", view_func=lambda reference: reference)

        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.user = Utilisateur(
            nom="Mode",
            prenom="Test",
            email="mode@example.com",
            telephone="+221700009999",
            mot_de_passe="hashed",
        )
        db.session.add(self.user)
        db.session.add(
            CompteSysteme(
                nom="Compte SN",
                fournisseur="Wave",
                pays="SN",
                numero="+221770000000",
                actif=True,
                solde=500000,
            )
        )
        db.session.add(Parametre(cle="platform_fee_rate", valeur="1.0"))
        db.session.commit()
        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["user_id"] = self.user.id

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _create_conversion(self, reference="CVT-PAY-01"):
        conversion = Conversion(
            user_id=self.user.id,
            from_currency="GNF",
            to_currency="CFA",
            montant_initial=1000,
            montant_converti=70,
            sender_phone="+224600000000",
            receiver_phone="+221770000000",
            reference=reference,
        )
        db.session.add(conversion)
        db.session.commit()
        return conversion

    def test_payment_mode_defaults_to_api(self):
        self.assertEqual(PaymentModeService.get_mode(), "api")

    def test_payment_mode_can_be_persisted(self):
        PaymentModeService.set_mode("manuel")
        db.session.commit()
        self.assertEqual(PaymentModeService.get_mode(), "manuel")

    def test_manual_mode_returns_manual_response(self):
        conversion = self._create_conversion("CVT-MAN-01")
        PaymentModeService.set_mode("manuel")
        db.session.commit()

        response = self.client.post(
            "/paiement/orange",
            json={"reference": conversion.reference, "telephone": "+221770000000"},
        )

        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["mode"], "manuel")
        self.assertIn("traitement manuel", payload["message"])

    def test_simulation_mode_returns_success_without_provider_api(self):
        conversion = self._create_conversion("CVT-SIM-01")
        PaymentModeService.set_mode("simulation")
        db.session.commit()

        response = self.client.post(
            "/paiement/wave",
            json={"reference": conversion.reference, "telephone": "+221770000000"},
        )

        payload = response.get_json()
        db.session.refresh(conversion)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["mode"], "simulation")
        self.assertEqual(conversion.statut, "valide")


if __name__ == "__main__":
    unittest.main()
