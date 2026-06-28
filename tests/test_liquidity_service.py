import unittest
from datetime import datetime, timedelta

from flask import Flask

from database import db
from models import (
    AdminUser,
    CompteSysteme,
    Conversion,
    Merchant,
    MerchantBalance,
    MerchantRate,
    Parametre,
    Settlement,
    Utilisateur,
    WalletEntry,
)
from services.liquidity_service import LiquidityService
from services.settlement_service import SettlementService


class LiquidityServiceTestCase(unittest.TestCase):
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

        db.session.add(Parametre(cle="platform_fee_rate", valeur="1.5"))
        db.session.add(
            CompteSysteme(
                nom="Compte Wave SN",
                fournisseur="Wave",
                pays="SN",
                numero="+221770000000",
                actif=True,
                solde=500000,
            )
        )
        db.session.add(
            CompteSysteme(
                nom="Compte Orange GN",
                fournisseur="Orange Money",
                pays="GN",
                numero="+224600000099",
                actif=True,
                solde=500000,
            )
        )
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _create_conversion(self, from_currency="CFA", to_currency="GNF", initial=1000, converted=15000):
        conversion = Conversion(
            from_currency=from_currency,
            to_currency=to_currency,
            montant_initial=initial,
            montant_converti=converted,
            sender_phone="+221700000001",
            receiver_phone="+224600000001",
            reference=f"CVT-{initial}-{converted}",
        )
        db.session.add(conversion)
        db.session.commit()
        return conversion

    def _create_admin(self):
        user = Utilisateur(
            nom="Admin",
            prenom="Root",
            email="admin@example.com",
            telephone="+221700000099",
            mot_de_passe="hashed",
            is_admin=True,
        )
        db.session.add(user)
        db.session.flush()
        admin = AdminUser(user_id=user.id, role="super_admin", actif=True)
        db.session.add(admin)
        db.session.commit()
        return admin

    def test_assigns_verified_merchant_and_reserves_funds(self):
        merchant = Merchant(
            code="MRC-GN-01",
            nom="Marchand Conakry",
            telephone="+224600000010",
            pays="GN",
            actif=True,
            verifie=True,
            risk_score=10,
            solde_disponible=50000,
        )
        db.session.add(merchant)
        db.session.flush()
        db.session.add(
            MerchantRate(
                merchant_id=merchant.id,
                from_currency="CFA",
                to_currency="GNF",
                rate=20.0,
                actif=True,
            )
        )
        db.session.commit()

        conversion = self._create_conversion()

        LiquidityService.assign_for_conversion(conversion)
        db.session.commit()

        self.assertEqual(conversion.liquidity_source_type, "merchant")
        self.assertEqual(conversion.risk_bearer, "merchant")
        self.assertEqual(conversion.settlement_status, "reserved")
        self.assertEqual(conversion.locked_amount, 15000)
        self.assertEqual(conversion.platform_fee, 225.0)
        self.assertIsNotNone(conversion.reserved_until)

        refreshed = db.session.get(Merchant, merchant.id)
        balance = MerchantBalance.query.filter_by(merchant_id=merchant.id, currency_code="GNF").first()
        self.assertEqual(refreshed.solde_disponible, 35000)
        self.assertEqual(refreshed.solde_verrouille, 15000)
        self.assertEqual(float(balance.available_balance), 35000.0)
        self.assertEqual(float(balance.locked_balance), 15000.0)
        self.assertEqual(float(balance.pending_balance), 0.0)

    def test_falls_back_to_platform_when_no_eligible_merchant(self):
        merchant = Merchant(
            code="MRC-GN-02",
            nom="Marchand Risque",
            telephone="+224600000011",
            pays="GN",
            actif=True,
            verifie=False,
            risk_score=90,
            solde_disponible=50000,
        )
        db.session.add(merchant)
        db.session.flush()
        db.session.add(
            MerchantRate(
                merchant_id=merchant.id,
                from_currency="CFA",
                to_currency="GNF",
                rate=16.0,
                actif=True,
            )
        )
        db.session.commit()

        conversion = self._create_conversion(initial=2000, converted=30000)

        LiquidityService.assign_for_conversion(conversion)
        db.session.commit()

        self.assertEqual(conversion.liquidity_source_type, "platform")
        self.assertEqual(conversion.risk_bearer, "platform")
        self.assertIsNotNone(conversion.compte_systeme_id)
        self.assertEqual(conversion.selection_reason, "platform_fallback")

    def test_releases_reserved_merchant_funds_on_failure(self):
        merchant = Merchant(
            code="MRC-GN-03",
            nom="Marchand Reserve",
            telephone="+224600000012",
            pays="GN",
            actif=True,
            verifie=True,
            risk_score=5,
            solde_disponible=40000,
        )
        db.session.add(merchant)
        db.session.flush()
        db.session.add(
            MerchantRate(
                merchant_id=merchant.id,
                from_currency="CFA",
                to_currency="GNF",
                rate=20.0,
                actif=True,
            )
        )
        db.session.commit()

        conversion = self._create_conversion(initial=1000, converted=10000)
        LiquidityService.assign_for_conversion(conversion)
        LiquidityService.finalize_conversion(conversion, success=False)
        db.session.commit()

        refreshed = db.session.get(Merchant, merchant.id)
        balance = MerchantBalance.query.filter_by(merchant_id=merchant.id, currency_code="GNF").first()
        self.assertEqual(conversion.statut, "echoue")
        self.assertEqual(conversion.settlement_status, "released")
        self.assertEqual(refreshed.solde_disponible, 40000)
        self.assertEqual(refreshed.solde_verrouille, 0)
        self.assertEqual(float(balance.available_balance), 40000.0)
        self.assertEqual(float(balance.locked_balance), 0.0)

    def test_creates_pending_settlement_on_success_and_completes_it(self):
        merchant = Merchant(
            code="MRC-GN-04",
            nom="Marchand Settlement",
            telephone="+224600000013",
            pays="GN",
            actif=True,
            verifie=True,
            risk_score=5,
            solde_disponible=80000,
        )
        db.session.add(merchant)
        db.session.flush()
        db.session.add(
            MerchantRate(
                merchant_id=merchant.id,
                from_currency="CFA",
                to_currency="GNF",
                rate=20.0,
                actif=True,
            )
        )
        db.session.commit()

        conversion = self._create_conversion(initial=1000, converted=20000)
        LiquidityService.assign_for_conversion(conversion)
        LiquidityService.finalize_conversion(conversion, success=True)
        db.session.commit()

        settlement = Settlement.query.filter_by(conversion_id=conversion.id).first()
        balance = MerchantBalance.query.filter_by(merchant_id=merchant.id, currency_code="GNF").first()
        self.assertIsNotNone(settlement)
        self.assertEqual(settlement.status, "pending")
        self.assertEqual(settlement.gross_amount, 20000)
        self.assertEqual(settlement.platform_fee, 300.0)
        self.assertEqual(settlement.net_amount, 19700.0)
        self.assertEqual(conversion.settlement_status, "ready_for_settlement")
        self.assertEqual(float(balance.available_balance), 60000.0)
        self.assertEqual(float(balance.locked_balance), 0.0)
        self.assertEqual(float(balance.pending_balance), 19700.0)

        admin = self._create_admin()
        SettlementService.complete_settlement(
            settlement=settlement,
            admin_id=admin.id,
            ip="127.0.0.1",
            notes="Paiement confirme",
        )
        db.session.commit()

        balance = MerchantBalance.query.filter_by(merchant_id=merchant.id, currency_code="GNF").first()
        self.assertEqual(settlement.status, "completed")
        self.assertEqual(settlement.approved_by_admin_id, admin.id)
        self.assertEqual(conversion.settlement_status, "completed")
        self.assertEqual(float(balance.pending_balance), 0.0)
        self.assertGreaterEqual(WalletEntry.query.filter_by(reference=settlement.reference).count(), 1)

    def test_expires_stale_reservations_and_restores_merchant_balance(self):
        merchant = Merchant(
            code="MRC-GN-05",
            nom="Marchand Timeout",
            telephone="+224600000014",
            pays="GN",
            actif=True,
            verifie=True,
            risk_score=5,
            solde_disponible=50000,
        )
        db.session.add(merchant)
        db.session.flush()
        db.session.add(
            MerchantRate(
                merchant_id=merchant.id,
                from_currency="CFA",
                to_currency="GNF",
                rate=20.0,
                actif=True,
            )
        )
        db.session.commit()

        conversion = self._create_conversion(initial=1000, converted=12000)
        LiquidityService.assign_for_conversion(conversion)
        conversion.statut = "paiement_en_cours"
        conversion.reserved_until = datetime.utcnow() - timedelta(minutes=1)
        db.session.commit()

        expired = LiquidityService.expire_stale_reservations()
        db.session.commit()

        refreshed = db.session.get(Merchant, merchant.id)
        balance = MerchantBalance.query.filter_by(merchant_id=merchant.id, currency_code="GNF").first()
        self.assertEqual(expired, [conversion.reference])
        self.assertEqual(conversion.statut, "echoue")
        self.assertEqual(conversion.settlement_status, "released")
        self.assertEqual(conversion.locked_amount, 0.0)
        self.assertIsNone(conversion.reserved_until)
        self.assertEqual(refreshed.solde_disponible, 50000)
        self.assertEqual(refreshed.solde_verrouille, 0.0)
        self.assertEqual(float(balance.available_balance), 50000.0)
        self.assertEqual(float(balance.locked_balance), 0.0)


if __name__ == "__main__":
    unittest.main()
