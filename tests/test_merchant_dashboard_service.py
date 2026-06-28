import unittest
from datetime import datetime, timedelta

from flask import Flask

from database import db
from models import Conversion, Currency, Dispute, Merchant, MerchantBalance, Settlement
from services.merchant_dashboard_service import MerchantDashboardService


class MerchantDashboardServiceTestCase(unittest.TestCase):
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
            code="MRC-DASH-01",
            nom="Marchand Dashboard",
            telephone="+224600000070",
            pays="GN",
            actif=True,
            verifie=True,
            solde_disponible=120000,
            solde_verrouille=8000,
        )
        db.session.add(self.merchant)
        db.session.flush()
        db.session.add(
            Currency(
                code="GNF",
                name="Guinean Franc",
                symbol="FG",
                decimal_places=0,
                is_active=True,
            )
        )
        db.session.add(
            MerchantBalance(
                merchant_id=self.merchant.id,
                currency_code="GNF",
                available_balance=120000,
                locked_balance=8000,
                pending_balance=0,
            )
        )

        now = datetime.utcnow()

        conv_success = Conversion(
            merchant_id=self.merchant.id,
            liquidity_source_type="merchant",
            risk_bearer="merchant",
            from_currency="CFA",
            to_currency="GNF",
            montant_initial=1000,
            montant_converti=15000,
            platform_fee=225,
            sender_phone="+2211",
            receiver_phone="+2241",
            reference="CVT-DASH-01",
            statut="valide",
            settlement_status="completed",
            date_conversion=now - timedelta(days=5),
        )
        conv_failed = Conversion(
            merchant_id=self.merchant.id,
            liquidity_source_type="merchant",
            risk_bearer="merchant",
            from_currency="CFA",
            to_currency="GNF",
            montant_initial=1000,
            montant_converti=10000,
            platform_fee=150,
            sender_phone="+2212",
            receiver_phone="+2242",
            reference="CVT-DASH-02",
            statut="echoue",
            settlement_status="released",
            date_conversion=now - timedelta(days=3),
        )
        conv_old = Conversion(
            merchant_id=self.merchant.id,
            liquidity_source_type="merchant",
            risk_bearer="merchant",
            from_currency="CFA",
            to_currency="GNF",
            montant_initial=1000,
            montant_converti=20000,
            platform_fee=300,
            sender_phone="+2213",
            receiver_phone="+2243",
            reference="CVT-DASH-03",
            statut="valide",
            settlement_status="completed",
            date_conversion=now - timedelta(days=40),
        )
        db.session.add_all([conv_success, conv_failed, conv_old])
        db.session.flush()

        db.session.add(
            Settlement(
                reference="STL-DASH-01",
                conversion_id=conv_success.id,
                merchant_id=self.merchant.id,
                gross_amount=15000,
                platform_fee=225,
                net_amount=14775,
                currency="GNF",
                status="completed",
                created_at=now - timedelta(days=5),
                settled_at=now - timedelta(days=4, hours=23),
            )
        )
        db.session.add(
            Settlement(
                reference="STL-DASH-03",
                conversion_id=conv_old.id,
                merchant_id=self.merchant.id,
                gross_amount=20000,
                platform_fee=300,
                net_amount=19700,
                currency="GNF",
                status="pending",
                created_at=now - timedelta(days=39),
            )
        )
        db.session.add(
            Dispute(
                reference="DSP-DASH-01",
                merchant_id=self.merchant.id,
                conversion_id=conv_failed.id,
                reason="Litige ouvert",
                status="open",
                created_at=now - timedelta(days=1),
            )
        )
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_snapshot_returns_expected_metrics(self):
        snapshot = MerchantDashboardService.snapshot(self.merchant)

        self.assertEqual(snapshot["solde_disponible"], 120000.0)
        self.assertEqual(snapshot["solde_verrouille"], 8000.0)
        self.assertEqual(snapshot["solde_pending"], 0.0)
        self.assertEqual(snapshot["volume_30_days"], 25000.0)
        self.assertEqual(snapshot["conversions_count"], 3)
        self.assertEqual(snapshot["success_rate"], 66.67)
        self.assertEqual(snapshot["open_disputes"], 1)
        self.assertEqual(snapshot["commissions_generated"], 525.0)
        self.assertEqual(snapshot["platform_fees_generated"], 525.0)
        self.assertEqual(snapshot["settlements_pending"], 1)
        self.assertEqual(snapshot["settlements_completed"], 1)
        self.assertGreater(snapshot["average_processing_minutes"], 0.0)
        self.assertEqual(len(snapshot["balance_breakdown"]), 1)
        self.assertEqual(snapshot["balance_breakdown"][0]["currency"], "GNF")
        self.assertEqual(snapshot["balance_breakdown"][0]["available_balance"], 120000.0)

        self.assertEqual(len(snapshot["currency_breakdown"]), 1)
        currency_row = snapshot["currency_breakdown"][0]
        self.assertEqual(currency_row["currency"], "GNF")
        self.assertEqual(currency_row["volume_30_days"], 25000.0)
        self.assertEqual(currency_row["conversions_count"], 3)
        self.assertEqual(currency_row["success_rate"], 66.67)
        self.assertEqual(currency_row["open_disputes"], 1)
        self.assertEqual(currency_row["commissions_generated"], 525.0)
        self.assertEqual(currency_row["settlements_pending"], 1)
        self.assertEqual(currency_row["settlements_completed"], 1)


if __name__ == "__main__":
    unittest.main()
