import unittest

from flask import Flask

from database import db
from models import AdminWalletAction, AuditLog, Currency, Merchant, MerchantBalance, WalletEntry
from services.merchant_wallet_admin_service import MerchantWalletAdminService
from services.wallet_service import WalletService


class MerchantWalletAdminServiceTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(
            TESTING=True,
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
            SECRET_KEY="test-secret",
        )
        db.init_app(self.app)
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
            code="MRC-ADMIN-WLT-01",
            nom="Merchant Admin Wallet",
            telephone="+224633333333",
            pays="GN",
            actif=True,
            verifie=True,
        )
        db.session.add(self.merchant)
        db.session.commit()

        WalletService.credit(
            merchant=self.merchant,
            currency="GNF",
            amount="10000",
            reference="SEED-001",
            description="Seed wallet",
            context={"provider": "seed"},
        )
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _balance(self):
        return MerchantBalance.query.filter_by(
            merchant_id=self.merchant.id,
            currency_code="GNF",
        ).first()

    def test_credit_wallet(self):
        MerchantWalletAdminService.execute(
            merchant=self.merchant,
            action="credit",
            currency="GNF",
            amount="2500",
            admin_user_id=99,
            ip_address="127.0.0.1",
            reason="Recharge",
            reference="ADM-CREDIT-001",
        )
        db.session.commit()
        self.assertEqual(float(self._balance().available_balance), 12500.0)

    def test_debit_wallet(self):
        MerchantWalletAdminService.execute(
            merchant=self.merchant,
            action="debit",
            currency="GNF",
            amount="2000",
            admin_user_id=99,
            ip_address="127.0.0.1",
            reason="Correction comptable",
            reference="ADM-DEBIT-001",
        )
        db.session.commit()
        self.assertEqual(float(self._balance().available_balance), 8000.0)

    def test_lock_wallet(self):
        MerchantWalletAdminService.execute(
            merchant=self.merchant,
            action="lock",
            currency="GNF",
            amount="3000",
            admin_user_id=99,
            ip_address="127.0.0.1",
            reason="Blocage precaution",
            reference="ADM-LOCK-001",
        )
        db.session.commit()
        self.assertEqual(float(self._balance().available_balance), 7000.0)
        self.assertEqual(float(self._balance().locked_balance), 3000.0)

    def test_unlock_wallet(self):
        MerchantWalletAdminService.execute(
            merchant=self.merchant,
            action="lock",
            currency="GNF",
            amount="3000",
            admin_user_id=99,
            ip_address="127.0.0.1",
            reason="Blocage precaution",
            reference="ADM-LOCK-002",
        )
        MerchantWalletAdminService.execute(
            merchant=self.merchant,
            action="unlock",
            currency="GNF",
            amount="1200",
            admin_user_id=99,
            ip_address="127.0.0.1",
            reason="Deblocage partiel",
            reference="ADM-UNLOCK-001",
        )
        db.session.commit()
        self.assertEqual(float(self._balance().available_balance), 8200.0)
        self.assertEqual(float(self._balance().locked_balance), 1800.0)

    def test_unknown_currency(self):
        with self.assertRaisesRegex(ValueError, "Devise inconnue ou inactive"):
            MerchantWalletAdminService.execute(
                merchant=self.merchant,
                action="credit",
                currency="XYZ",
                amount="100",
                admin_user_id=99,
                ip_address="127.0.0.1",
                reason="Test",
            )

    def test_negative_amount(self):
        with self.assertRaisesRegex(ValueError, "strictement positif"):
            MerchantWalletAdminService.execute(
                merchant=self.merchant,
                action="credit",
                currency="GNF",
                amount="-10",
                admin_user_id=99,
                ip_address="127.0.0.1",
                reason="Test",
            )

    def test_missing_reason(self):
        with self.assertRaisesRegex(ValueError, "motif est obligatoire"):
            MerchantWalletAdminService.execute(
                merchant=self.merchant,
                action="credit",
                currency="GNF",
                amount="10",
                admin_user_id=99,
                ip_address="127.0.0.1",
                reason="",
            )

    def test_missing_reference(self):
        result = MerchantWalletAdminService.execute(
            merchant=self.merchant,
            action="credit",
            currency="GNF",
            amount="10",
            admin_user_id=99,
            ip_address="127.0.0.1",
            reason="Reference auto",
        )
        db.session.commit()
        self.assertTrue(result["reference"].startswith("ADMIN-CREDIT-"))

    def test_audit_created(self):
        MerchantWalletAdminService.execute(
            merchant=self.merchant,
            action="credit",
            currency="GNF",
            amount="100",
            admin_user_id=99,
            ip_address="127.0.0.1",
            reason="Recharge",
            reference="ADM-AUDIT-001",
        )
        db.session.commit()
        audit = AuditLog.query.filter_by(event="merchant_wallet_credit").first()
        admin_action = AdminWalletAction.query.filter_by(reference="ADM-AUDIT-001").first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor_id, 99)
        self.assertIsNotNone(admin_action)
        self.assertEqual(admin_action.requested_by_admin_id, 99)

    def test_wallet_entry_created(self):
        MerchantWalletAdminService.execute(
            merchant=self.merchant,
            action="credit",
            currency="GNF",
            amount="500",
            admin_user_id=99,
            ip_address="127.0.0.1",
            reason="Bonus",
            reference="ADM-ENTRY-001",
        )
        db.session.commit()
        self.assertEqual(WalletEntry.query.filter_by(reference="ADM-ENTRY-001").count(), 1)

    def test_high_amount_requires_confirmation(self):
        with self.assertRaisesRegex(ValueError, "Confirmation explicite requise"):
            MerchantWalletAdminService.execute(
                merchant=self.merchant,
                action="credit",
                currency="GNF",
                amount="1000000",
                admin_user_id=99,
                ip_address="127.0.0.1",
                reason="Topup sensible",
                reference="ADM-HIGH-001",
            )

        MerchantWalletAdminService.execute(
            merchant=self.merchant,
            action="credit",
            currency="GNF",
            amount="1000000",
            admin_user_id=99,
            ip_address="127.0.0.1",
            reason="Topup sensible",
            reference="ADM-HIGH-002",
            high_amount_confirmed=True,
        )
        db.session.commit()
        self.assertIsNotNone(AdminWalletAction.query.filter_by(reference="ADM-HIGH-002").first())


if __name__ == "__main__":
    unittest.main()
