from engines.profitability_engine.calculator import ProfitabilityCalculator


class ProfitabilityEngine:
    @staticmethod
    def analyse(input_data):
        return ProfitabilityCalculator.calculer(input_data)
