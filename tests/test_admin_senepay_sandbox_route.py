import os
import unittest
from unittest.mock import patch

from flask import Flask

from database import db
from routes.admin import admin


class AdminSenePaySandboxRouteTestCase(unittest.TestCase):
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
            SENEPAY_MODE="sandbox",
            SENEPAY_BASE_URL="https://api.sene-pay.com",
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

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_admin_can_access_sandbox_page(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["is_admin"] = True

        response = self.client.get("/admin/senepay-sandbox")
        self.assertEqual(response.status_code, 200)

    def test_non_admin_cannot_access_sandbox_page(self):
        with self.client.session_transaction() as session:
            session["user_id"] = 2
            session["is_admin"] = False

        response = self.client.get("/admin/senepay-sandbox")
        self.assertEqual(response.status_code, 302)

    @patch("routes.admin.SenePaySandboxTestService.recent_logs", return_value=[])
    @patch("routes.admin.SenePaySandboxTestService.execute_action")
    def test_admin_post_executes_sandbox_service(self, execute_action, _recent_logs):
        execute_action.return_value = {
            "success": True,
            "message": "ok",
            "reference_interne": "SBX-001",
            "reference_provider": "tok_123",
            "statut_senepay": "pending",
            "operation": "payin_direct_create",
            "trace": {"action": "create_direct_payin"},
            "payload": {},
        }

        with self.client.session_transaction() as session:
            session["user_id"] = 1
            session["is_admin"] = True

        response = self.client.post(
            "/admin/senepay-sandbox",
            data={
                "action": "create_direct_payin",
                "amount": "1000",
                "currency": "XOF",
                "phone_number": "+221770000000",
            },
        )

        self.assertEqual(response.status_code, 200)
        execute_action.assert_called_once()


if __name__ == "__main__":
    unittest.main()
