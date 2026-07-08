import unittest
from unittest.mock import Mock, patch

from flask import Flask

from database import db
from models import AuditLog
from services.senepay_sandbox_test_service import SenePaySandboxTestService


class SenePaySandboxTestServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SECRET_KEY="test-secret",
            SENEPAY_MODE="sandbox",
            SENEPAY_BASE_URL="https://api.sene-pay.com",
            SENEPAY_PUBLIC_KEY="pk_test_example",
            SENEPAY_SECRET_KEY="sk_test_example",
            SENEPAY_WEBHOOK_SECRET="whsec_test_example",
        )
        db.init_app(self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    @patch("services.senepay_sandbox_test_service.ProviderFactory.create")
    def test_execute_action_creates_audit_log(self, factory_create):
        fake_provider = Mock()
        fake_provider.get_wallet_balance.return_value = {
            "success": True,
            "operation": "wallet_balance",
            "reference": None,
            "status": "ok",
            "message": "Balance recue",
            "payload": {
                "request": {"url": "https://api.sene-pay.com/api/v1/merchant/wallet/balance"},
                "response": {"available": 1000},
                "http_status_code": 200,
            },
        }
        factory_create.return_value = fake_provider

        result = SenePaySandboxTestService.execute_action(
            action="get_wallet_balance",
            payload={},
            admin_user_id=12,
            ip_address="127.0.0.1",
        )
        db.session.commit()

        self.assertTrue(result["success"])
        self.assertEqual(result["statut_senepay"], "ok")
        self.assertEqual(AuditLog.query.filter_by(event="senepay_sandbox_get_wallet_balance").count(), 1)


if __name__ == "__main__":
    unittest.main()
