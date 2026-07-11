# Matrice de Tracabilite

## Objectif

Cette matrice relie chaque regle metier a :

- son document d'origine,
- son futur service d'implementation,
- ses tests.

Elle permet de s'assurer qu'aucune logique critique n'est codee sans origine metier explicite.

## Matrice Initiale

| Regle metier | Document | Service cible | Tests cibles |
| --- | --- | --- | --- |
| Priorite a la liquidite propre | `REGLES_METIER_FINANCIERES.md` | `BusinessEngine` / `liquidity_policy_evaluator` | `test_business_engine.py` |
| Marge minimale | `PRICING_FORMULAS.md` | `BusinessEngine` / `margin_policy_service` | `test_business_engine.py` |
| Politique par tranche | `REGLES_METIER_FINANCIERES.md` | `margin_policy_service` | `test_margin_policy_service.py` |
| Segmentation VIP | `SEGMENTATION_CLIENTS.md` | `client_segmentation_service` | `test_client_segmentation_service.py` |
| Decision metier explicable | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `BusinessEngine` | `test_business_engine.py` |
| Corridor + direction | `ADR-004-corridor-direction-pricing.md` | `BusinessEngine` | `test_business_engine.py` |
| Mode hybride | `ADR-005-liquidity-orchestrator.md` | `liquidity_policy_evaluator` | `test_liquidity_policy_evaluator.py` |
| Flux strategique recurrent | `SEGMENTATION_CLIENTS.md` | `client_segmentation_service` / `BusinessEngine` | `test_client_segmentation_service.py` |

## Ajouts - Business Engine minimal

| Regle metier | Document | Service cible | Tests cibles |
| --- | --- | --- | --- |
| Separation marche client / marche fournisseur | `SEPARATION_MARCHE_CLIENT_MARCHE_FOURNISSEUR.md` | `engines/business_engine/business_engine.py` | `test_business_engine_models.py` |
| Offre client | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/models.py` | `test_business_engine_models.py` |
| Cout de liquidite | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/liquidity_cost_evaluator.py` | `test_business_engine_models.py` |
| Marge cible | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/margin_calculator.py` | `test_business_engine_models.py` |
| Politique commerciale | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/models.py` / `engines/business_engine/business_engine.py` | `test_business_engine_xof_gnf_scenario.py` |
| Plan d'execution | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/execution_planner.py` | `test_business_engine_models.py` |
| Premier scenario XOF -> GNF | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` | `test_business_engine_xof_gnf_scenario.py` |
| Client regulier | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` | `test_business_engine_xof_gnf_scenario.py` |
| Client VIP | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` | `test_business_engine_xof_gnf_scenario.py` |
| Refus automatique marge negative | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` | `test_business_engine_xof_gnf_scenario.py` |
| Validation manuelle / surveillance | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` | `test_business_engine_models.py` / `test_business_engine_xof_gnf_scenario.py` |
| Classification du flux | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/models.py` / `engines/business_engine/business_engine.py` | `test_business_engine_xof_gnf_scenario.py` |
| Priorite d'execution | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/liquidity_cost_evaluator.py` | `test_business_engine_xof_gnf_scenario.py` |
| Signaux de preparation Treasury | `MODELE_OBJETS_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` | `test_business_engine_xof_gnf_scenario.py` |
| Tresorerie courante simulee | `MODELE_OBJETS_BUSINESS_ENGINE.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/business_engine/models.py` | `test_business_engine_treasury_bridge.py` |
| Treasury snapshot | `MODELE_OBJETS_BUSINESS_ENGINE.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/business_engine/treasury_bridge.py` | `test_business_engine_treasury_bridge.py` |
| Treasury requirement | `MODELE_OBJETS_BUSINESS_ENGINE.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` / `engines/business_engine/treasury_bridge.py` | `test_business_engine_treasury_bridge.py` |
| Treasury assessment | `MODELE_OBJETS_BUSINESS_ENGINE.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/business_engine/treasury_bridge.py` | `test_business_engine_treasury_bridge.py` |
| Protection de la reserve minimale | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/business_engine/treasury_bridge.py` | `test_business_engine_treasury_bridge.py` |
| Recours marchand / fournisseur / hybride | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/business_engine/treasury_bridge.py` | `test_business_engine_treasury_bridge.py` |
| Scenario complet offre -> Treasury -> decision -> plan | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` | `test_business_engine_v04_simulation.py` |
| Offre client figee pendant l'optimisation interne | `SEPARATION_MARCHE_CLIENT_MARCHE_FOURNISSEUR.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` | `test_business_engine_v04_simulation.py` |
| Validation manuelle ou refus selon politique de liquidite | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` | `test_business_engine_v04_simulation.py` |
| Snapshot construit depuis soldes reels simules | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` / `MODELE_OBJETS_BUSINESS_ENGINE.md` | `services/treasury_snapshot_builder.py` | `test_execution_reservation_service.py` |
| LiquidityRepository abstrait | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/liquidity_repository.py` | `test_execution_reservation_service.py` |
| Reservation transactionnelle de liquidite | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` / `MODELE_OBJETS_BUSINESS_ENGINE.md` | `services/execution_reservation_service.py` | `test_execution_reservation_service.py` |
| Revalidation de liquidite avant lock | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/execution_reservation_service.py` | `test_execution_reservation_service.py` |
| Rollback complet sur echec partiel | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/execution_reservation_service.py` | `test_execution_reservation_service.py` |
| Idempotence par transaction_reference | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/execution_reservation_service.py` / `models.py` | `test_execution_reservation_service.py` |
| Protection de la reserve minimale au lock | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/execution_reservation_service.py` | `test_execution_reservation_service.py` |
| Isolation stricte par devise au lock | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/execution_reservation_service.py` | `test_execution_reservation_service.py` |
| Business Engine sans dependance SQLAlchemy ni WalletService | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/business_engine/business_engine.py` | `test_execution_reservation_service.py` |
| Orchestration applicative d'une conversion | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` / `MODELE_OBJETS_BUSINESS_ENGINE.md` | `services/conversion_orchestration_service.py` | `test_conversion_orchestration_service.py` |
| Offre client figee pendant toute la conversion | `SEPARATION_MARCHE_CLIENT_MARCHE_FOURNISSEUR.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/conversion_orchestration_service.py` | `test_conversion_orchestration_service.py` |
| Refus avant reservation si marge negative | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/conversion_orchestration_service.py` | `test_conversion_orchestration_service.py` |
| Echec de reservation sans mutation de l'offre | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/conversion_orchestration_service.py` / `services/execution_reservation_service.py` | `test_conversion_orchestration_service.py` |
| Idempotence par reference de conversion | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/conversion_orchestration_service.py` / `models.py` | `test_conversion_orchestration_service.py` |
| Expiration et annulation de conversion | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/conversion_orchestration_service.py` | `test_conversion_orchestration_service.py` |
| Orchestration d'execution controlee | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` / `MODELE_OBJETS_BUSINESS_ENGINE.md` | `services/conversion_execution_service.py` | `test_conversion_execution_service.py` |
| Mode simulation / manuel / api | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/execution_adapters.py` / `services/conversion_execution_service.py` | `test_conversion_execution_service.py` |
| Pending verification non traite comme echec | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/execution_adapters.py` / `services/conversion_execution_service.py` | `test_conversion_execution_service.py` |
| Double confirmation sans double mouvement | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/conversion_execution_service.py` | `test_conversion_execution_service.py` |
| Separation stricte service metier / SenePay | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/conversion_execution_service.py` | `test_conversion_execution_service.py` |
| Tracabilite conversion -> reservation -> execution -> wallet -> audit | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `services/conversion_execution_service.py` / `models.py` | `test_conversion_execution_service.py` |
| Rentabilite reelle par conversion | `PROFITABILITY_KPIS.md` / `PRICING_FORMULAS.md` | `engines/profitability_engine/profitability_engine.py` | `test_profitability_engine.py` |
| Ecart entre marge estimee et marge reelle | `PROFITABILITY_KPIS.md` / `PRICING_FORMULAS.md` | `engines/profitability_engine/calculator.py` | `test_profitability_engine.py` |
| Transaction en perte / critique / acceptable | `PROFITABILITY_KPIS.md` | `engines/profitability_engine/enums.py` / `engines/profitability_engine/calculator.py` | `test_profitability_engine.py` |
| Rentabilite provisoire et couts non recuperables | `PROFITABILITY_KPIS.md` | `engines/profitability_engine/calculator.py` | `test_profitability_engine.py` |
| Isolation stricte du moteur de rentabilite | `PROFITABILITY_KPIS.md` | `engines/profitability_engine/` | `test_profitability_engine.py` |
| Reporting par corridor | `PROFITABILITY_KPIS.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/reporting_engine/reporting_engine.py` | `test_reporting_engine.py` |
| Reporting par marchand | `PROFITABILITY_KPIS.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/reporting_engine/reporting_engine.py` / `services/reporting_service.py` | `test_reporting_engine.py` / `test_reporting_service.py` |
| Reporting par client | `PROFITABILITY_KPIS.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/reporting_engine/reporting_engine.py` / `services/reporting_service.py` | `test_reporting_engine.py` / `test_reporting_service.py` |
| Reporting par devise | `PROFITABILITY_KPIS.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/reporting_engine/reporting_engine.py` | `test_reporting_engine.py` |
| Reporting par mode d'execution | `PROFITABILITY_KPIS.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/reporting_engine/reporting_engine.py` | `test_reporting_engine.py` |
| Reporting par segment client | `PROFITABILITY_KPIS.md` / `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` | `engines/reporting_engine/reporting_engine.py` | `test_reporting_engine.py` |
| Transformation Conversion / Execution / Profitability en KPI lisibles | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` / `PROFITABILITY_KPIS.md` | `services/reporting_service.py` | `test_reporting_service.py` |
| Dashboard admin read-only de reporting | `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` / `PROFITABILITY_KPIS.md` | `services/reporting_service.py` / `routes/admin.py` | `test_reporting_service.py` / `test_admin_reporting_route.py` |
| Validation fonctionnelle controlee du reporting | `VALIDATION_FONCTIONNELLE_EPIC_8_9_REPORTING.md` | `services/reporting_service.py` / `engines/reporting_engine/reporting_engine.py` | `test_reporting_validation_integration.py` |

## Regle de Maintien

Chaque nouveau service metier critique devra etre ajoute a cette matrice avant ou pendant son implementation.
