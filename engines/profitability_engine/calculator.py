from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from engines.profitability_engine.enums import ProfitabilityLevel
from engines.profitability_engine.models import ProfitabilityInput, ProfitabilityResult


class ProfitabilityCalculator:
    HUNDRED = Decimal("100")

    @staticmethod
    def calculer(input_data: ProfitabilityInput) -> ProfitabilityResult:
        revenu_brut = ProfitabilityCalculator._revenu_brut(input_data)
        cout_total_estime = ProfitabilityCalculator._cout_total_estime(input_data)
        cout_total_reel = ProfitabilityCalculator._cout_total_reel(input_data)
        marge_brute_estimee = revenu_brut - input_data.cout_liquidite_estime
        marge_brute_reelle = revenu_brut - input_data.cout_liquidite_reel
        marge_nette_reelle = revenu_brut - cout_total_reel
        ecart_prevision_reel = marge_nette_reelle - input_data.marge_estimee
        taux_marge_nette = ProfitabilityCalculator._taux_marge_nette(
            marge_nette_reelle=marge_nette_reelle,
            valeur_reference=input_data.montant_destination_client,
        )
        niveau = ProfitabilityCalculator._niveau_rentabilite(
            marge_nette_reelle=marge_nette_reelle,
            taux_marge_nette=taux_marge_nette,
        )
        motif = ProfitabilityCalculator._motif(
            input_data=input_data,
            niveau=niveau,
            marge_nette_reelle=marge_nette_reelle,
            ecart_prevision_reel=ecart_prevision_reel,
        )
        return ProfitabilityResult(
            revenu_brut=revenu_brut,
            cout_total_estime=cout_total_estime,
            cout_total_reel=cout_total_reel,
            marge_brute_estimee=marge_brute_estimee,
            marge_brute_reelle=marge_brute_reelle,
            marge_nette_reelle=marge_nette_reelle,
            ecart_prevision_reel=ecart_prevision_reel,
            taux_marge_nette=taux_marge_nette,
            profitable=marge_nette_reelle >= 0,
            niveau_rentabilite=niveau,
            motif=motif,
            calculated_at=datetime.utcnow(),
            provisoire=input_data.provisoire,
        )

    @staticmethod
    def _revenu_brut(input_data: ProfitabilityInput) -> Decimal:
        return (
            input_data.cout_liquidite_estime
            + input_data.marge_estimee
            + input_data.commissions_client
            + input_data.commissions_marchand
        )

    @staticmethod
    def _cout_total_estime(input_data: ProfitabilityInput) -> Decimal:
        return input_data.cout_liquidite_estime

    @staticmethod
    def _cout_total_reel(input_data: ProfitabilityInput) -> Decimal:
        return (
            input_data.cout_liquidite_reel
            + input_data.frais_payin_reels
            + input_data.frais_payout_reels
            + input_data.frais_marchand_reels
            + input_data.autres_couts_reels
        )

    @staticmethod
    def _taux_marge_nette(*, marge_nette_reelle: Decimal, valeur_reference: Decimal) -> Decimal:
        if not valeur_reference:
            return Decimal("0")
        return (
            (marge_nette_reelle / valeur_reference) * ProfitabilityCalculator.HUNDRED
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _niveau_rentabilite(*, marge_nette_reelle: Decimal, taux_marge_nette: Decimal) -> ProfitabilityLevel:
        if marge_nette_reelle < 0:
            return ProfitabilityLevel.PERTE
        if taux_marge_nette < Decimal("0.50"):
            return ProfitabilityLevel.CRITIQUE
        if taux_marge_nette < Decimal("1.50"):
            return ProfitabilityLevel.FAIBLE
        if taux_marge_nette < Decimal("3.00"):
            return ProfitabilityLevel.ACCEPTABLE
        if taux_marge_nette < Decimal("5.00"):
            return ProfitabilityLevel.BONNE
        return ProfitabilityLevel.EXCELLENTE

    @staticmethod
    def _motif(*, input_data: ProfitabilityInput, niveau: ProfitabilityLevel, marge_nette_reelle: Decimal, ecart_prevision_reel: Decimal) -> str:
        if input_data.annulee:
            return "Conversion annulee avec couts non recuperables"
        if input_data.remboursee:
            return "Conversion remboursee avec impact financier residuel"
        if input_data.provisoire:
            return "Rentabilite provisoire en attente de confirmation finale"
        if niveau == ProfitabilityLevel.PERTE:
            return "Transaction en perte"
        if ecart_prevision_reel < 0:
            return "Marge reelle inferieure a la marge estimee"
        if marge_nette_reelle > input_data.marge_estimee:
            return "Marge reelle superieure a la marge estimee"
        return "Rentabilite conforme aux attentes"
