import unittest
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Flask

from database import db
from models import Conversion, ConversionExecution, Merchant, Utilisateur
from services.reporting_service import ReportingService


class ReportingValidationIntegrationTestCase(unittest.TestCase):
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

        self.user_regular = Utilisateur(
            nom="Diallo",
            prenom="Moussa",
            email="moussa.validation@example.com",
            telephone="+224600000401",
            mot_de_passe="secret",
        )
        self.user_vip = Utilisateur(
            nom="Bah",
            prenom="Aicha",
            email="aicha.validation@example.com",
            telephone="+224600000402",
            mot_de_passe="secret",
        )
        self.merchant_a = Merchant(
            code="MR-VAL-01",
            nom="Aladji",
            telephone="+224600000403",
            pays="GN",
            actif=True,
            verifie=True,
        )
        self.merchant_b = Merchant(
            code="MR-VAL-02",
            nom="SeneMerchant",
            telephone="+221700000404",
            pays="SN",
            actif=True,
            verifie=True,
        )
        db.session.add_all([self.user_regular, self.user_vip, self.merchant_a, self.merchant_b])
        db.session.flush()

        now = datetime.utcnow()
        self._create_case(
            reference="CNV-VAL-001",
            user_id=self.user_regular.id,
            merchant_id=None,
            from_currency="XOF",
            to_currency="GNF",
            source_amount="10000",
            target_amount="150000",
            margin_estimated="5000",
            execution_cost="1000",
            execution_mode="platform",
            liquidity_source_type="platform",
            status="completed",
            execution_status="completed",
            corridor="SN-GN",
            segment="standard",
            classification="ponctuel",
            created_at=now - timedelta(days=2),
            completed_at=now - timedelta(days=2, minutes=-4),
        )
        self._create_case(
            reference="CNV-VAL-002",
            user_id=self.user_regular.id,
            merchant_id=self.merchant_a.id,
            from_currency="GNF",
            to_currency="XOF",
            source_amount="4500000",
            target_amount="262000",
            margin_estimated="10000",
            execution_cost="30000",
            execution_mode="merchant",
            liquidity_source_type="merchant",
            status="completed",
            execution_status="completed",
            corridor="GN-SN",
            segment="regulier",
            classification="recurrent",
            created_at=now - timedelta(days=1),
            completed_at=now - timedelta(days=1, minutes=-7),
        )
        self._create_case(
            reference="CNV-VAL-003",
            user_id=self.user_vip.id,
            merchant_id=self.merchant_a.id,
            from_currency="XOF",
            to_currency="GNF",
            source_amount="12000",
            target_amount="180000",
            margin_estimated="12000",
            execution_cost="3000",
            execution_mode="hybrid",
            liquidity_source_type="hybrid",
            status="payout_processing",
            execution_status="payout_processing",
            corridor="SN-GN",
            segment="vip",
            classification="strategique",
            created_at=now - timedelta(hours=10),
            completed_at=None,
        )
        self._create_case(
            reference="CNV-VAL-004",
            user_id=self.user_vip.id,
            merchant_id=None,
            from_currency="EUR",
            to_currency="GNF",
            source_amount="50",
            target_amount="500000",
            margin_estimated="15000",
            execution_cost="5000",
            execution_mode="platform",
            liquidity_source_type="platform",
            status="completed",
            execution_status="completed",
            corridor="EU-GN",
            segment="vip",
            classification="vip",
            created_at=now - timedelta(hours=8),
            completed_at=now - timedelta(hours=7, minutes=50),
        )
        self._create_case(
            reference="CNV-VAL-005",
            user_id=self.user_regular.id,
            merchant_id=self.merchant_b.id,
            from_currency="USD",
            to_currency="XOF",
            source_amount="100",
            target_amount="61000",
            margin_estimated="3000",
            execution_cost="500",
            execution_mode="merchant",
            liquidity_source_type="merchant",
            status="completed",
            execution_status="completed",
            corridor="US-SN",
            segment="entreprise",
            classification="strategique",
            created_at=now - timedelta(hours=6),
            completed_at=now - timedelta(hours=5, minutes=55),
        )
        self._create_case(
            reference="CNV-VAL-006",
            user_id=self.user_vip.id,
            merchant_id=self.merchant_b.id,
            from_currency="GNF",
            to_currency="USD",
            source_amount="3000000",
            target_amount="200",
            margin_estimated="25",
            execution_cost="10",
            execution_mode="hybrid",
            liquidity_source_type="hybrid",
            status="completed",
            execution_status="completed",
            corridor="GN-US",
            segment="vip",
            classification="recurrent",
            created_at=now - timedelta(hours=4),
            completed_at=now - timedelta(hours=3, minutes=50),
        )
        self._create_case(
            reference="CNV-VAL-007",
            user_id=self.user_regular.id,
            merchant_id=None,
            from_currency="XOF",
            to_currency="GNF",
            source_amount="7000",
            target_amount="105000",
            margin_estimated="4000",
            execution_cost="0",
            execution_mode="platform",
            liquidity_source_type="platform",
            status="cancelled",
            execution_status="cancelled",
            corridor="SN-GN",
            segment="standard",
            classification="ponctuel",
            created_at=now - timedelta(hours=3),
            completed_at=now - timedelta(hours=2, minutes=55),
        )
        self._create_case(
            reference="CNV-VAL-008",
            user_id=self.user_regular.id,
            merchant_id=None,
            from_currency="XOF",
            to_currency="GNF",
            source_amount="8000",
            target_amount="120000",
            margin_estimated="5000",
            execution_cost="0",
            execution_mode="platform",
            liquidity_source_type="platform",
            status="rejected",
            execution_status="rejected",
            corridor="SN-GN",
            segment="standard",
            classification="ponctuel",
            created_at=now - timedelta(hours=2),
            completed_at=now - timedelta(hours=1, minutes=55),
        )
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _create_case(
        self,
        *,
        reference,
        user_id,
        merchant_id,
        from_currency,
        to_currency,
        source_amount,
        target_amount,
        margin_estimated,
        execution_cost,
        execution_mode,
        liquidity_source_type,
        status,
        execution_status,
        corridor,
        segment,
        classification,
        created_at,
        completed_at,
    ):
        conversion = Conversion(
            user_id=user_id,
            merchant_id=merchant_id,
            from_currency=from_currency,
            to_currency=to_currency,
            montant_initial=float(Decimal(source_amount)),
            montant_converti=float(Decimal(target_amount)),
            reference=reference,
            statut=status,
            liquidity_source_type=liquidity_source_type,
            quote_source_amount=Decimal(source_amount),
            quote_target_amount=Decimal(target_amount),
            client_rate=Decimal("1.00"),
            margin_estimated=Decimal(margin_estimated),
            execution_mode=execution_mode,
            date_conversion=created_at,
            offer_snapshot={
                "corridor": corridor,
                "segment_client": segment,
                "classification_flux": classification,
            },
        )
        db.session.add(conversion)
        db.session.flush()
        db.session.add(
            ConversionExecution(
                conversion_id=conversion.id,
                execution_reference=f"EXE-{reference}",
                mode=execution_mode,
                provider_code="",
                status=execution_status,
                amount_source=Decimal(source_amount),
                amount_destination=Decimal(target_amount),
                provider_fees=Decimal("0"),
                execution_cost=Decimal(execution_cost),
                started_at=created_at + timedelta(minutes=1),
                completed_at=completed_at,
            )
        )

    def test_controlled_dataset_matches_expected_values_case_by_case(self):
        rows = ReportingService.build_rows()
        by_ref = {row.conversion_reference: row for row in rows}

        expected = {
            "CNV-VAL-001": {"marge_estimee": Decimal("5000"), "marge_nette": Decimal("4000"), "ecart": Decimal("-1000"), "corridor": "SN-GN", "devise": "GNF", "segment": "standard", "mode": "platform", "provisoire": False},
            "CNV-VAL-002": {"marge_estimee": Decimal("10000"), "marge_nette": Decimal("-20000"), "ecart": Decimal("-30000"), "corridor": "GN-SN", "devise": "XOF", "segment": "regulier", "mode": "merchant", "provisoire": False},
            "CNV-VAL-003": {"marge_estimee": Decimal("12000"), "marge_nette": Decimal("9000"), "ecart": Decimal("-3000"), "corridor": "SN-GN", "devise": "GNF", "segment": "vip", "mode": "hybrid", "provisoire": True},
            "CNV-VAL-004": {"marge_estimee": Decimal("15000"), "marge_nette": Decimal("10000"), "ecart": Decimal("-5000"), "corridor": "EU-GN", "devise": "GNF", "segment": "vip", "mode": "platform", "provisoire": False},
            "CNV-VAL-005": {"marge_estimee": Decimal("3000"), "marge_nette": Decimal("2500"), "ecart": Decimal("-500"), "corridor": "US-SN", "devise": "XOF", "segment": "entreprise", "mode": "merchant", "provisoire": False},
            "CNV-VAL-006": {"marge_estimee": Decimal("25"), "marge_nette": Decimal("15"), "ecart": Decimal("-10"), "corridor": "GN-US", "devise": "USD", "segment": "vip", "mode": "hybrid", "provisoire": False},
        }

        for reference, expected_values in expected.items():
            row = by_ref[reference]
            self.assertEqual(row.marge_estimee, expected_values["marge_estimee"])
            self.assertEqual(row.marge_nette, expected_values["marge_nette"])
            self.assertEqual(row.ecart_prevision_reel, expected_values["ecart"])
            self.assertEqual(row.corridor, expected_values["corridor"])
            self.assertEqual(row.devise_cible, expected_values["devise"])
            self.assertEqual(row.segment_client, expected_values["segment"])
            self.assertEqual(row.execution_mode, expected_values["mode"])
            self.assertEqual(row.provisoire, expected_values["provisoire"])

    def test_loss_provisional_modes_and_filters_are_consistent(self):
        dashboard = ReportingService.generate_dashboard()
        self.assertEqual(dashboard["totaux"]["conversions_count"], 8)
        self.assertEqual(dashboard["totaux"]["pertes_count"], 1)
        self.assertEqual(dashboard["totaux"]["provisoires_count"], 1)
        self.assertEqual(dashboard["totaux"]["definitives_count"], 7)

        loss_refs = {row.conversion_reference for row in dashboard["transactions_en_perte"]}
        self.assertEqual(loss_refs, {"CNV-VAL-002"})

        provisional_refs = {row.conversion_reference for row in dashboard["conversions_provisoires"]}
        self.assertEqual(provisional_refs, {"CNV-VAL-003"})

        merchant_filtered = ReportingService.generate_dashboard(execution_mode="merchant")
        self.assertEqual(merchant_filtered["totaux"]["conversions_count"], 2)

        hybrid_filtered = ReportingService.generate_dashboard(execution_mode="hybrid")
        self.assertEqual(hybrid_filtered["totaux"]["conversions_count"], 2)

        corridor_filtered = ReportingService.generate_dashboard(corridor="SN-GN")
        self.assertEqual(corridor_filtered["totaux"]["conversions_count"], 4)

        currency_filtered = ReportingService.generate_dashboard(currency="USD")
        self.assertEqual(currency_filtered["totaux"]["conversions_count"], 2)

        status_filtered = ReportingService.generate_dashboard(statut="completed")
        self.assertEqual(status_filtered["totaux"]["conversions_count"], 5)

        merchant_id_filtered = ReportingService.generate_dashboard(merchant_id=self.merchant_a.id)
        self.assertEqual(merchant_id_filtered["totaux"]["conversions_count"], 2)

    def test_cancelled_and_rejected_are_counted_once_and_do_not_create_false_losses(self):
        dashboard = ReportingService.generate_dashboard()
        rows = {row.conversion_reference: row for row in dashboard["rows"]}

        self.assertEqual(rows["CNV-VAL-007"].marge_nette, Decimal("4000"))
        self.assertEqual(rows["CNV-VAL-008"].marge_nette, Decimal("5000"))
        self.assertEqual(dashboard["totaux"]["pertes_count"], 1)

        snapshot = dashboard["snapshot"]
        corridor_map = {row.corridor: row for row in snapshot.corridor_rows}
        self.assertEqual(corridor_map["SN-GN"].conversions_count, 4)

    def test_base_vide_returns_zeroed_dashboard(self):
        ConversionExecution.query.delete()
        Conversion.query.delete()
        db.session.commit()

        dashboard = ReportingService.generate_dashboard()
        self.assertEqual(dashboard["totaux"]["conversions_count"], 0)
        self.assertEqual(dashboard["totaux"]["marge_nette"], Decimal("0"))
        self.assertEqual(dashboard["totaux"]["pertes_count"], 0)
        self.assertEqual(len(dashboard["snapshot"].corridor_rows), 0)
        self.assertEqual(len(dashboard["rows"]), 0)

    def test_dashboard_generation_does_not_write_or_mutate(self):
        before = (
            Conversion.query.count(),
            ConversionExecution.query.count(),
            db.session.query(db.func.sum(Conversion.montant_converti)).scalar(),
        )
        ReportingService.generate_dashboard()
        after = (
            Conversion.query.count(),
            ConversionExecution.query.count(),
            db.session.query(db.func.sum(Conversion.montant_converti)).scalar(),
        )
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
