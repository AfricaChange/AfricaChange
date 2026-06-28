import unittest
import os

from flask import Flask

from database import db
from models import AuditLog, Currency, Merchant, WalletEntry
from routes.admin import admin


class AdminMerchantWalletRouteTestCase(unittest.TestCase):
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

        db.session.add(
            Currency(
                code="GNF",
                name="Guinean Franc",
                symbol="FG",
                decimal_places=0,
                is_active=True,
            )
        )
        self.merchant = Merchant(
            code="MRC-ROUTE-01",
            nom="Route Merchant",
            telephone="+224644444444",
            pays="GN",
            actif=True,
            verifie=True,
        )
        db.session.add(self.merchant)
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_admin_can_access_wallet_page(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["is_admin"] = True

        response = self.client.get(f"/admin/marchands/{self.merchant.id}/wallet")
        self.assertEqual(response.status_code, 200)

    def test_non_admin_cannot_access_wallet_page(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 2
            session["is_admin"] = False

        response = self.client.get(f"/admin/marchands/{self.merchant.id}/wallet")
        self.assertEqual(response.status_code, 302)

    def test_non_admin_cannot_post_wallet_operation(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 2
            session["is_admin"] = False

        response = self.client.post(
            f"/admin/marchands/{self.merchant.id}/wallet",
            data={
                "action": "credit",
                "currency": "GNF",
                "amount": "100",
                "reason": "Intrusion",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(WalletEntry.query.count(), 0)

    def test_admin_post_creates_wallet_entry_and_audit(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["is_admin"] = True

        response = self.client.post(
            f"/admin/marchands/{self.merchant.id}/wallet",
            data={
                "action": "credit",
                "currency": "GNF",
                "amount": "1500",
                "reference": "ADM-ROUTE-001",
                "reason": "Recharge sandbox",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(WalletEntry.query.filter_by(reference="ADM-ROUTE-001").count(), 1)
        self.assertIsNotNone(AuditLog.query.filter_by(event="merchant_wallet_credit").first())


if __name__ == "__main__":
    unittest.main()
