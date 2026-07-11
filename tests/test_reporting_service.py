import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Flask

from database import db
from models import Conversion, ConversionExecution, Merchant, Utilisateur
from services.reporting_service import ReportingService


class ReportingServiceTestCase(unittest.TestCase):
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

        self.user = Utilisateur(
            nom="Diallo",
            prenom="Moussa",
            email="moussa@example.com",
            telephone="+224600000111",
            mot_de_passe="secret",
        )
        self.merchant = Merchant(
            code="MR-REPORT-01",
            nom="Aladji",
            telephone="+224600000112",
            pays="GN",
            actif=True,
            verifie=True,
        )
        db.session.add_all([self.user, self.merchant])
        db.session.flush()

        conversion_1 = Conversion(
            user_id=self.user.id,
            merchant_id=self.merchant.id,
            from_currency="XOF",
            to_currency="GNF",
            montant_initial=5000,
            montant_converti=75000,
            reference="CNV-SVC-001",
            statut="completed",
            liquidity_source_type="merchant",
            quote_source_amount=Decimal("5000"),
            quote_target_amount=Decimal("75000"),
            client_rate=Decimal("15.00"),
            margin_estimated=Decimal("4000"),
            execution_mode="merchant",
            date_conversion=datetime.utcnow() - timedelta(minutes=15),
            offer_snapshot={
                "corridor": "SN-GN",
                "segment_client": "regulier",
                "classification_flux": "recurrent",
            },
        )
        conversion_2 = Conversion(
            user_id=self.user.id,
            from_currency="GNF",
            to_currency="XOF",
            montant_initial=4500000,
            montant_converti=262000,
            reference="CNV-SVC-002",
            statut="manual_review_required",
            liquidity_source_type="platform",
            quote_source_amount=Decimal("4500000"),
            quote_target_amount=Decimal("262000"),
            client_rate=Decimal("17.18"),
            margin_estimated=Decimal("124000"),
            execution_mode="platform",
            date_conversion=datetime.utcnow() - timedelta(minutes=10),
            offer_snapshot={
                "corridor": "GN-SN",
                "segment_client": "vip",
                "classification_flux": "strategique",
            },
        )
        db.session.add_all([conversion_1, conversion_2])
        db.session.flush()

        db.session.add(
            ConversionExecution(
                conversion_id=conversion_1.id,
                execution_reference="EXE-SVC-001",
                mode="merchant",
                provider_code="",
                status="completed",
                amount_source=Decimal("5000"),
                amount_destination=Decimal("75000"),
                provider_fees=Decimal("250"),
                execution_cost=Decimal("1750"),
                started_at=datetime.utcnow() - timedelta(minutes=12),
                completed_at=datetime.utcnow() - timedelta(minutes=5),
            )
        )
        db.session.add(
            ConversionExecution(
                conversion_id=conversion_2.id,
                execution_reference="EXE-SVC-002",
                mode="platform",
                provider_code="",
                status="manual_review_required",
                amount_source=Decimal("4500000"),
                amount_destination=Decimal("262000"),
                provider_fees=Decimal("0"),
                execution_cost=Decimal("30000"),
                started_at=datetime.utcnow() - timedelta(minutes=9),
                completed_at=None,
            )
        )
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_build_rows_derive_profitability_and_incidents(self):
        rows = ReportingService.build_rows()
        rows_by_ref = {row.conversion_reference: row for row in rows}

        merchant_row = rows_by_ref["CNV-SVC-001"]
        self.assertEqual(merchant_row.corridor, "SN-GN")
        self.assertEqual(merchant_row.merchant_code, "MR-REPORT-01")
        self.assertEqual(merchant_row.client_nom, "Moussa Diallo")
        self.assertEqual(merchant_row.marge_nette, Decimal("2250"))
        self.assertFalse(merchant_row.incident)

        platform_row = rows_by_ref["CNV-SVC-002"]
        self.assertEqual(platform_row.execution_mode, "platform")
        self.assertTrue(platform_row.incident)
        self.assertEqual(platform_row.segment_client, "vip")

    def test_generate_snapshot_returns_all_dimensions(self):
        snapshot = ReportingService.generate_snapshot()

        self.assertEqual(len(snapshot.corridor_rows), 2)
        self.assertEqual(len(snapshot.merchant_rows), 1)
        self.assertEqual(len(snapshot.client_rows), 1)
        self.assertGreaterEqual(len(snapshot.currency_rows), 2)
        self.assertEqual(len(snapshot.execution_mode_rows), 2)
        self.assertEqual(len(snapshot.segment_rows), 2)

        merchant_row = snapshot.merchant_rows[0]
        self.assertEqual(merchant_row.merchant_code, "MR-REPORT-01")
        self.assertEqual(merchant_row.marge_nette, Decimal("2250"))

    def test_generate_dashboard_supports_filters_and_provisional_split(self):
        dashboard = ReportingService.generate_dashboard(
            corridor="SN-GN",
            execution_mode="merchant",
            statut="completed",
        )

        self.assertEqual(dashboard["totaux"]["conversions_count"], 1)
        self.assertEqual(dashboard["totaux"]["provisoires_count"], 0)
        self.assertEqual(dashboard["totaux"]["definitives_count"], 1)
        self.assertEqual(len(dashboard["snapshot"].corridor_rows), 1)
        self.assertEqual(dashboard["snapshot"].corridor_rows[0].corridor, "SN-GN")

    def test_generate_dashboard_identifies_rows_below_forecast(self):
        dashboard = ReportingService.generate_dashboard()
        references = {row.conversion_reference for row in dashboard["transactions_sous_prevision"]}
        self.assertIn("CNV-SVC-001", references)
        self.assertIn("CNV-SVC-002", references)

    def test_no_write_is_performed_during_dashboard_generation(self):
        before = Conversion.query.count(), ConversionExecution.query.count()
        ReportingService.generate_dashboard()
        after = Conversion.query.count(), ConversionExecution.query.count()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
