class ReconciliationEngine:
    @staticmethod
    def describe_scope():
        return {
            "sources": [
                "africachangex_ledger",
                "provider_wallet",
                "mobile_money_transactions",
            ]
        }
