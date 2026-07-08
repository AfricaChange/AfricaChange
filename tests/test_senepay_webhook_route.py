import hashlib
import hmac
import json
import unittest

from flask import Flask

from database import db
from models import AuditLog, PaymentEvent
from webhook import webhook_bp


class SenePayWebhookRouteTestCase(unittest.TestCase):
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
        self.app.register_blueprint(webhook_bp)
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _signed_payload(self):
        payload = {
            "event": "checkout.session.completed",
            "sessionToken": "chk_test_001",
            "orderReference": "ACX-SBX-CHK-001",
            "status": "Complete",
            "transactionId": "SENEPAY_PAYIN_001",
            "fees": 180,
            "netAmount": 4820,
            "timestamp": "2026-07-08T12:30:00Z",
        }
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(
            b"whsec_test_example",
            raw,
            hashlib.sha256,
        ).hexdigest()
        return payload, raw, signature

    def test_webhook_records_event_and_audit(self):
        _, raw, signature = self._signed_payload()
        response = self.client.post(
            "/webhooks/senepay",
            data=raw,
            headers={
                "Content-Type": "application/json",
                "X-SenePay-Signature": signature,
                "X-SenePay-Event": "checkout.session.completed",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PaymentEvent.query.count(), 1)
        self.assertEqual(AuditLog.query.filter_by(event="senepay_webhook_received").count(), 1)

    def test_webhook_is_idempotent_for_duplicate_payload(self):
        _, raw, signature = self._signed_payload()
        headers = {
            "Content-Type": "application/json",
            "X-SenePay-Signature": signature,
            "X-SenePay-Event": "checkout.session.completed",
        }

        first = self.client.post("/webhooks/senepay", data=raw, headers=headers)
        second = self.client.post("/webhooks/senepay", data=raw, headers=headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(PaymentEvent.query.count(), 1)

    def test_invalid_signature_is_rejected(self):
        payload = {"event": "checkout.session.completed", "sessionToken": "chk_invalid"}
        response = self.client.post(
            "/webhooks/senepay",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-SenePay-Signature": "bad-signature",
                "X-SenePay-Event": "checkout.session.completed",
            },
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(PaymentEvent.query.count(), 0)


if __name__ == "__main__":
    unittest.main()
