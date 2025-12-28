from models import Transaction, RiskLog, Refund
from database import db
from sqlalchemy import func

class AdminDashboardService:

    @staticmethod
    def snapshot():
        return {
            "transactions": {
                "pending": Transaction.query.filter_by(statut="en_attente").count(),
                "blocked": Transaction.query.filter_by(statut="bloque").count(),
                "success": Transaction.query.filter_by(statut="valide").count(),
            },
            "refunds": {
                "total": Refund.query.count(),
            },
            "risks": {
                "alerts": RiskLog.query.count()
            },
            "volume": {
                "total": db.session.query(func.sum(Transaction.montant)).scalar() or 0
            }
        }
