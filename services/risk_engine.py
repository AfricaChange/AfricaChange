from datetime import datetime, timedelta
from models import Transaction, RiskEvent
from database import db


class RiskEngine:

    HIGH_RISK = 70
    MEDIUM_RISK = 40

    @staticmethod
    def score_transaction(tx, ip: str) -> int:
        score = 0

        # 🔴 Paiement rapide répété
        recent = Transaction.query.filter(
            Transaction.ip_address == ip,
            Transaction.date_transaction >= datetime.utcnow() - timedelta(minutes=5)
        ).count()

        if recent >= 3:
            score += 40

        # 🔴 Montant élevé
        if tx.montant > 200_000:
            score += 30

        # 🔴 Compte non connecté
        if not tx.user_id:
            score += 20

        return score

    @staticmethod
    def log(reference, provider, ip, risk_type, score, details):
        event = RiskEvent(
            reference=reference,
            provider=provider,
            ip_address=ip,
            risk_type=risk_type,
            risk_score=score,
            details=details
        )
        db.session.add(event)
