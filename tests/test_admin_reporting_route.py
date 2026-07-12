import os
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Flask

from database import db
from models import Conversion, ConversionExecution, Merchant, Utilisateur
from routes.admin import admin


class AdminReportingRouteTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(
            __name__,
            template_folder=os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "templates",
            ),
        )
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SECRET_KEY="test-secret",
            WTF_CSRF_ENABLED=False,
            SERVER_NAME="localhost",
        )
        db.init_app(self.app)
        self.app.register_blueprint(admin)

        @self.app.context_processor
        def inject_globals():
            return {"csrf_token": lambda: "test-csrf"}

        @self.app.route("/")
        def home():
            return "home"

        self.app.add_url_rule("/", endpoint="main.accueil", view_func=home)

        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

        user = Utilisateur(
            nom="Camara",
            prenom="Aminata",
            email="aminata@example.com",
            telephone="+224600000301",
            mot_de_passe="secret",
        )
        merchant = Merchant(
            code="MR-ADMIN-REP-01",
            nom="Marchand Reporting",
            telephone="+224600000302",
            pays="GN",
            actif=True,
            verifie=True,
        )
        db.session.add_all([user, merchant])
        db.session.flush()

        conversion = Conversion(
            user_id=user.id,
            merchant_id=merchant.id,
            from_currency="XOF",
            to_currency="GNF",
            montant_initial=5000,
            montant_converti=75000,
            reference="CNV-ADM-REP-001",
            statut="completed",
            liquidity_source_type="merchant",
            quote_source_amount=Decimal("5000"),
            quote_target_amount=Decimal("75000"),
            client_rate=Decimal("15.00"),
            margin_estimated=Decimal("4000"),
            execution_mode="merchant",
            date_conversion=datetime.utcnow() - timedelta(minutes=10),
            offer_snapshot={
                "corridor": "SN-GN",
                "segment_client": "regulier",
                "classification_flux": "recurrent",
            },
        )
        db.session.add(conversion)
        db.session.flush()
        db.session.add(
            ConversionExecution(
                conversion_id=conversion.id,
                execution_reference="EXE-ADM-REP-001",
                mode="simulation",
                provider_code="",
                status="completed",
                amount_source=Decimal("5000"),
                amount_destination=Decimal("75000"),
                provider_fees=Decimal("250"),
                execution_cost=Decimal("1750"),
                started_at=datetime.utcnow() - timedelta(minutes=8),
                completed_at=datetime.utcnow() - timedelta(minutes=2),
            )
        )
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_admin_can_access_reporting_page(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["is_admin"] = True

        response = self.client.get("/admin/reporting")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Reporting financier".encode("utf-8"), response.data)

    def test_non_admin_cannot_access_reporting_page(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 2
            session["is_admin"] = False

        response = self.client.get("/admin/reporting")
        self.assertEqual(response.status_code, 302)

    def test_reporting_page_supports_empty_state(self):
        ConversionExecution.query.delete()
        Conversion.query.delete()
        db.session.commit()

        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["is_admin"] = True

        response = self.client.get("/admin/reporting")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Aucune donnee".encode("utf-8"), response.data)


if __name__ == "__main__":
    unittest.main()
