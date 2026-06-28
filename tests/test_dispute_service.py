import unittest

from flask import Flask

from database import db
from models import AdminUser, Conversion, Dispute, Merchant, Paiement, Transaction, Utilisateur
from services.dispute_service import DisputeService


class DisputeServiceTestCase(unittest.TestCase):
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
            nom="User",
            prenom="One",
            email="user@example.com",
            telephone="+221700000001",
            mot_de_passe="hashed",
        )
        db.session.add(self.user)
        db.session.flush()

        admin_user = Utilisateur(
            nom="Admin",
            prenom="Root",
            email="admin2@example.com",
            telephone="+221700000099",
            mot_de_passe="hashed",
            is_admin=True,
        )
        db.session.add(admin_user)
        db.session.flush()
        self.admin = AdminUser(user_id=admin_user.id, role="super_admin", actif=True)
        db.session.add(self.admin)

        self.merchant = Merchant(
            code="MRC-DSP-01",
            nom="Marchand Litige",
            telephone="+224600000050",
            pays="GN",
            actif=True,
            verifie=True,
            risk_score=5,
            solde_disponible=30000,
        )
        db.session.add(self.merchant)
        db.session.flush()

        self.conversion = Conversion(
            user_id=self.user.id,
            from_currency="CFA",
            to_currency="GNF",
            montant_initial=1000,
            montant_converti=15000,
            sender_phone="+221700000001",
            receiver_phone="+224600000099",
            reference="CVT-DSP-01",
            liquidity_source_type="merchant",
            risk_bearer="merchant",
            merchant_id=self.merchant.id,
        )
        db.session.add(self.conversion)
        db.session.flush()

        self.tx = Transaction(
            user_id=self.user.id,
            type="paiement",
            montant=1000,
            statut="en_attente",
            fournisseur="Wave",
            reference="TX-DSP-01",
        )
        db.session.add(self.tx)
        db.session.flush()

        self.paiement = Paiement(
            conversion_id=self.conversion.id,
            montant_envoye=1000,
            montant_recu=15000,
            devise_source="CFA",
            devise_cible="GNF",
            sender_phone="+221700000001",
            receiver_phone="+224600000099",
            statut="en_attente",
            transaction_reference=self.tx.reference,
            idempotency_key="idem-dsp-01",
        )
        db.session.add(self.paiement)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_open_dispute_can_suspend_merchant(self):
        dispute = DisputeService.open_transaction_dispute(
            tx=self.tx,
            admin_id=self.admin.id,
            ip="127.0.0.1",
            reason="preuve insuffisante",
            details="controle manuel",
            suspend_merchant=True,
        )
        db.session.commit()

        merchant = db.session.get(Merchant, self.merchant.id)
        self.assertEqual(dispute.status, "open")
        self.assertEqual(dispute.merchant_id, self.merchant.id)
        self.assertFalse(merchant.actif)
        self.assertIsNotNone(merchant.suspended_at)

    def test_resolve_dispute_marks_it_resolved(self):
        dispute = DisputeService.open_transaction_dispute(
            tx=self.tx,
            admin_id=self.admin.id,
            ip="127.0.0.1",
            reason="ecart marchand",
            suspend_merchant=False,
        )
        db.session.commit()

        DisputeService.resolve_dispute(
            dispute=dispute,
            admin_id=self.admin.id,
            ip="127.0.0.1",
            resolution_note="controle termine",
        )
        db.session.commit()

        self.assertEqual(dispute.status, "resolved")
        self.assertEqual(dispute.resolved_by_admin_id, self.admin.id)
        self.assertIsNotNone(dispute.resolved_at)

    def test_reinstate_merchant_restores_active_flag(self):
        DisputeService.suspend_merchant(
            merchant=self.merchant,
            admin_id=self.admin.id,
            ip="127.0.0.1",
            reason="fraude suspectee",
        )
        db.session.commit()

        DisputeService.reinstate_merchant(
            merchant=self.merchant,
            admin_id=self.admin.id,
            ip="127.0.0.1",
            reason="controle ok",
        )
        db.session.commit()

        merchant = db.session.get(Merchant, self.merchant.id)
        self.assertTrue(merchant.actif)
        self.assertIsNone(merchant.suspended_at)
        self.assertIsNone(merchant.suspension_reason)


if __name__ == "__main__":
    unittest.main()
