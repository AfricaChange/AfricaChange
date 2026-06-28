class PricingEngine:
    @staticmethod
    def quote(*, provider_fee=0.0, platform_margin=0.0, merchant_commission=0.0, gross_amount=0.0):
        total_fees = float(provider_fee or 0.0) + float(platform_margin or 0.0) + float(merchant_commission or 0.0)
        net_amount = round(float(gross_amount or 0.0) - total_fees, 2)
        return {
            "provider_fee": round(float(provider_fee or 0.0), 2),
            "platform_margin": round(float(platform_margin or 0.0), 2),
            "merchant_commission": round(float(merchant_commission or 0.0), 2),
            "gross_amount": round(float(gross_amount or 0.0), 2),
            "net_amount": net_amount,
        }
