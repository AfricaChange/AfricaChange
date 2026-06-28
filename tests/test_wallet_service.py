import unittest

from flask import Flask

from database import db
from models import Merchant, MerchantBalance, WalletEntry
from services.wallet_service import WalletService


class WalletServiceTestCase(unittest.TestCase):
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

        self.merchant = Merchant(
            code="MRC-WALLET-01",
            nom="Merchant Wallet",
            telephone="+224611111111",
            pays="GN",
            actif=True,
            verifie=True,
            solde_disponible=1000,
        )
        self.other_merchant = Merchant(
            code="MRC-WALLET-02",
            nom="Merchant Wallet 2",
            telephone="+224622222222",
            pays="GN",
            actif=True,
            verifie=True,
        )
        db.session.add_all([self.merchant, self.other_merchant])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_credit_lock_unlock_and_clear_pending_are_currency_scoped(self):
        WalletService.credit(
            merchant=self.merchant,
            currency="USD",
            amount="25.50",
            reference="WLT-001",
            context={"provider": "manual"},
        )
        WalletService.lock(
            merchant=self.merchant,
            currency="USD",
            amount="10.50",
            reference="WLT-002",
        )
        WalletService.unlock(
            merchant=self.merchant,
            currency="USD",
            amount="2.00",
            reference="WLT-003",
        )
        WalletService.lock_to_pending(
            merchant=self.merchant,
            currency="USD",
            gross_amount="8.50",
            net_amount="8.00",
            reference="WLT-004",
            context={"platform_fee": "0.50"},
        )
        WalletService.clear_pending(
            merchant=self.merchant,
            currency="USD",
            amount="8.00",
            reference="WLT-005",
        )
        db.session.commit()

        usd_balance = MerchantBalance.query.filter_by(merchant_id=self.merchant.id, currency_code="USD").first()
        gnf_balance = MerchantBalance.query.filter_by(merchant_id=self.merchant.id, currency_code="GNF").first()

        self.assertIsNotNone(usd_balance)
        self.assertIsNone(gnf_balance)
        self.assertEqual(float(usd_balance.available_balance), 1017.0)
        self.assertEqual(float(usd_balance.locked_balance), 0.0)
        self.assertEqual(float(usd_balance.pending_balance), 0.0)
        self.assertEqual(WalletEntry.query.count(), 8)

    def test_transfer_moves_funds_between_merchants(self):
        WalletService.credit(
            merchant=self.merchant,
            currency="GNF",
            amount="5000",
            reference="WLT-TRF-01",
        )
        WalletService.transfer(
            source_merchant=self.merchant,
            destination_merchant=self.other_merchant,
            currency="GNF",
            amount="1250",
            reference="WLT-TRF-02",
        )
        db.session.commit()

        source = MerchantBalance.query.filter_by(merchant_id=self.merchant.id, currency_code="GNF").first()
        destination = MerchantBalance.query.filter_by(merchant_id=self.other_merchant.id, currency_code="GNF").first()

        self.assertEqual(float(source.available_balance), 4750.0)
        self.assertEqual(float(destination.available_balance), 1250.0)


if __name__ == "__main__":
    unittest.main()
