import unittest
from datetime import datetime
from decimal import Decimal

from engines.reporting_engine import ReportingEngine, ReportingInputRow


class ReportingEngineTestCase(unittest.TestCase):
    def _row(self, **overrides):
        base = {
            "conversion_reference": "CNV-REP-001",
            "corridor": "SN-GN",
            "merchant_code": "MR-01",
            "merchant_nom": "Aladji",
            "client_reference": "USR-1",
            "client_nom": "Client VIP",
            "segment_client": "vip",
            "classification_flux": "recurrent",
            "devise_source": "XOF",
            "devise_cible": "GNF",
            "execution_mode": "merchant",
            "liquidity_source_type": "merchant",
            "provider_code": "",
            "statut": "completed",
            "montant_source": Decimal("5000"),
            "montant_destination": Decimal("75000"),
            "revenu_brut": Decimal("79000"),
            "marge_estimee": Decimal("4000"),
            "marge_nette": Decimal("2250"),
            "execution_cost": Decimal("1750"),
            "provider_fees": Decimal("250"),
            "delai_execution_minutes": Decimal("7"),
            "profitable": True,
            "incident": False,
            "created_at": datetime(2026, 7, 11, 0, 0, 0),
        }
        base.update(overrides)
        return ReportingInputRow(**base)

    def test_aggregation_par_corridor(self):
        snapshot = ReportingEngine.generer(
            [
                self._row(),
                self._row(
                    conversion_reference="CNV-REP-002",
                    montant_source=Decimal("200000"),
                    montant_destination=Decimal("3000000"),
                    revenu_brut=Decimal("3112500"),
                    marge_nette=Decimal("77500"),
                    marge_estimee=Decimal("92500"),
                ),
            ]
        )

        corridor = snapshot.corridor_rows[0]
        self.assertEqual(corridor.corridor, "SN-GN")
        self.assertEqual(corridor.conversions_count, 2)
        self.assertEqual(corridor.profitable_count, 2)
        self.assertEqual(corridor.volume_source, Decimal("205000"))
        self.assertEqual(corridor.volume_destination, Decimal("3075000"))
        self.assertEqual(corridor.marge_nette, Decimal("79750"))

    def test_aggregation_par_marchand_avec_score(self):
        snapshot = ReportingEngine.generer(
            [
                self._row(),
                self._row(
                    conversion_reference="CNV-REP-003",
                    montant_destination=Decimal("29700000"),
                    revenu_brut=Decimal("29856000"),
                    marge_nette=Decimal("96000"),
                    marge_estimee=Decimal("96000"),
                    delai_execution_minutes=Decimal("8"),
                ),
            ]
        )

        merchant_row = snapshot.merchant_rows[0]
        self.assertEqual(merchant_row.merchant_code, "MR-01")
        self.assertEqual(merchant_row.conversions_count, 2)
        self.assertEqual(merchant_row.score, "A")
        self.assertEqual(merchant_row.incidents_count, 0)

    def test_aggregation_par_client_calcule_la_frequence(self):
        rows = [
            self._row(conversion_reference=f"CNV-REP-10{i}") for i in range(3)
        ]
        snapshot = ReportingEngine.generer(rows)

        client_row = snapshot.client_rows[0]
        self.assertEqual(client_row.client_reference, "USR-1")
        self.assertEqual(client_row.conversions_count, 3)
        self.assertEqual(client_row.frequence, "moyenne")
        self.assertEqual(client_row.classification_dominante, "recurrent")

    def test_aggregation_par_devise_isole_source_et_cible(self):
        snapshot = ReportingEngine.generer(
            [
                self._row(),
                self._row(
                    conversion_reference="CNV-REP-004",
                    devise_source="GNF",
                    devise_cible="XOF",
                    montant_source=Decimal("4500000"),
                    montant_destination=Decimal("262000"),
                    revenu_brut=Decimal("4346000"),
                    marge_nette=Decimal("124000"),
                ),
            ]
        )

        currencies = {row.currency_code: row for row in snapshot.currency_rows}
        self.assertEqual(currencies["XOF"].volume_source, Decimal("5000"))
        self.assertEqual(currencies["XOF"].volume_destination, Decimal("262000"))
        self.assertEqual(currencies["GNF"].volume_source, Decimal("4500000"))
        self.assertEqual(currencies["GNF"].volume_destination, Decimal("75000"))

    def test_aggregation_par_mode_execution(self):
        snapshot = ReportingEngine.generer(
            [
                self._row(),
                self._row(
                    conversion_reference="CNV-REP-005",
                    execution_mode="platform",
                    liquidity_source_type="platform",
                    provider_fees=Decimal("0"),
                    execution_cost=Decimal("0"),
                    revenu_brut=Decimal("29856000"),
                    marge_nette=Decimal("96000"),
                ),
            ]
        )

        modes = {row.execution_mode: row for row in snapshot.execution_mode_rows}
        self.assertEqual(modes["merchant"].conversions_count, 1)
        self.assertEqual(modes["platform"].conversions_count, 1)
        self.assertEqual(modes["merchant"].provider_fees, Decimal("250"))

    def test_aggregation_par_segment_client(self):
        snapshot = ReportingEngine.generer(
            [
                self._row(segment_client="vip"),
                self._row(conversion_reference="CNV-REP-006", segment_client="vip"),
                self._row(conversion_reference="CNV-REP-007", segment_client="standard"),
            ]
        )

        segments = {row.segment_client: row for row in snapshot.segment_rows}
        self.assertEqual(segments["vip"].conversions_count, 2)
        self.assertEqual(segments["standard"].conversions_count, 1)


if __name__ == "__main__":
    unittest.main()
