import unittest
from unittest.mock import Mock

import requests

from providers.senepay_provider import SenePayProvider


class SenePayProviderTestCase(unittest.TestCase):
    def _provider_with_session(self, session):
        return SenePayProvider(
            mode="sandbox",
            base_url="https://api.sene-pay.com",
            public_key="pk_test_example",
            secret_key="sk_test_example",
            webhook_secret="whsec_test_example",
            session=session,
        )

    def test_create_checkout_session_calls_expected_endpoint(self):
        session = Mock()
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.reason = "OK"
        response.json.return_value = {
            "status": "pending",
            "sessionToken": "sess_123",
            "message": "Session creee",
        }
        session.request.return_value = response

        provider = self._provider_with_session(session)
        result = provider.create_checkout_session(
            reference="CHK-001",
            amount="1200",
            currency="XOF",
            success_url="https://www.africachangex.com/payment-success",
            cancel_url="https://www.africachangex.com/payment-cancel",
            webhook_url="https://www.africachangex.com/webhooks/senepay",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["operation"], "checkout_session_create")
        self.assertEqual(result["reference"], "sess_123")
        session.request.assert_called_once()
        _, kwargs = session.request.call_args
        self.assertEqual(kwargs["method"], "POST")
        self.assertEqual(kwargs["url"], "https://api.sene-pay.com/api/v1/checkout/sessions")
        self.assertEqual(kwargs["json"]["OrderReference"], "CHK-001")
        self.assertNotIn("reference", kwargs["json"])
        self.assertEqual(kwargs["json"]["amount"], "1200")
        self.assertEqual(kwargs["json"]["currency"], "XOF")
        self.assertEqual(kwargs["json"]["successUrl"], "https://www.africachangex.com/payment-success")
        self.assertEqual(kwargs["json"]["cancelUrl"], "https://www.africachangex.com/payment-cancel")
        self.assertEqual(kwargs["json"]["webhookUrl"], "https://www.africachangex.com/webhooks/senepay")

    def test_wallet_balance_uses_balance_endpoint(self):
        session = Mock()
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.reason = "OK"
        response.json.return_value = {
            "status": "ok",
            "available": 1000,
        }
        session.request.return_value = response

        provider = self._provider_with_session(session)
        result = provider.get_wallet_balance()

        self.assertTrue(result["success"])
        self.assertEqual(result["operation"], "wallet_balance")
        _, kwargs = session.request.call_args
        self.assertEqual(kwargs["method"], "GET")
        self.assertEqual(kwargs["url"], "https://api.sene-pay.com/api/v1/merchant/wallet/balance")

    def test_create_payout_extracts_disbursement_reference(self):
        session = Mock()
        response = Mock()
        response.ok = True
        response.status_code = 200
        response.reason = "OK"
        response.json.return_value = {
            "status": "submitted",
            "disbursement_id": "DISB_A1B2C3",
            "external_id": "PAY-001",
            "message": "Payout initiated successfully",
        }
        session.request.return_value = response

        provider = self._provider_with_session(session)
        result = provider.create_payout(
            external_id="PAY-001",
            amount="25000",
            phone="221771234567",
            country="SN",
            operator="wave",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["reference"], "DISB_A1B2C3")
        self.assertEqual(result["status"], "submitted")

    def test_request_exception_is_normalized(self):
        session = Mock()
        session.request.side_effect = requests.RequestException("timeout test")

        provider = self._provider_with_session(session)
        result = provider.get_direct_payin_status("tok_123")

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "request_error")
        self.assertIn("timeout test", result["message"])


if __name__ == "__main__":
    unittest.main()
