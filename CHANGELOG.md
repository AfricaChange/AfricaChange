# Changelog

## 2026-06-28
- creation des documents de gouvernance manquants a la racine
- introduction du squelette modulaire `providers/`
- introduction du squelette modulaire `engines/`
- introduction du squelette modulaire `webhooks/`
- ajout d'un registre provider et d'une factory provider de base
- ajout d'un provider `SenePay` de reference

## 2026-06-28 - Gouvernance architecture renforcee
- ajout de la gouvernance par EPIC dans `PROJECT_MASTER.md`
- formalisation des ADR sur `Decimal`, wallets, provider adapter et revue obligatoire
- ajout de `docs/architecture/ARCHITECT_REVIEW.md`

## 2026-06-28 - Passage en Phase 2
- formalisation de `Phase 2 - Infrastructure Fintech`
- ajout de la vision produit panafricaine
- ajout du cadre `Core / Business / Interfaces`
- ajout de l'EPIC 9 `Core financier`
- ajout de l'approche par domaines metier

## 2026-06-28 - EPIC 8 multi-currency wallet
- ajout de `Currency`, `MerchantBalance` et `WalletEntry`
- ajout du `WalletTransactionManager` et du `WalletService`
- branchement de la liquidite marchand et des settlements sur le wallet multi-devises
- ajout d'une migration wallet multi-devises
- ajout des tests wallet, liquidite et dashboard

## 2026-06-28 - EPIC 8.5 wallet administration
- ajout de `merchant_wallet_admin_service.py` pour les operations admin wallet
- ajout de la route admin `marchands/<id>/wallet` et de la page `admin_merchant_wallet.html`
- ajout de `AdminWalletAction` pour tracer les actions admin wallet
- ajout des controles: motif obligatoire, devise active, reference garantie, confirmation sur montant sensible
- ajout de l'historique admin wallet dans l'interface
- ajout des tests unitaires et d'integration admin wallet

## 2026-06-28 - EPIC 8.6 repository cleanup and certification
- creation des rapports `TECH_DEBT.md`, `LEGACY.md` et `REPOSITORY_HEALTH.md`
- correction de `.gitignore` pour Python / Flask
- correction des references cassees des assets admin
- marquage explicite du legacy sur `convert.py` et dependances associees
- suppression des artefacts Python generes (`__pycache__`, `.pyc`)
- correction verifiee de la route support et ajout de tests dedies
- certification interne `Fintech Foundation v0.9`

## 2026-07-08 - EPIC SenePay Sandbox Phase 1
- remplacement du provider `SenePay` placeholder par une integration Sandbox structuree via `providers/senepay_provider.py`
- ajout des appels techniques Sandbox : checkout session, statut checkout, payin direct, statut payin, wallet balance, estimation payout, payout simple, statut payout
- ajout du service interne `services/senepay_sandbox_test_service.py`
- ajout de la page admin `/admin/senepay-sandbox` pour tester l'integration technique sans logique metier AfricaChangeX
- ajout des traces techniques et audits admin pour les tests Sandbox SenePay
- ajout des tests unitaires mock HTTP pour le provider et des tests du service/route admin

## 2026-07-09 - Separation marche client / marche fournisseur
- formalisation de la separation entre marche visible client et marche interne fournisseur
- ajout de `docs/business/SEPARATION_MARCHE_CLIENT_MARCHE_FOURNISSEUR.md`
- ajout de `docs/decisions/ADR-006-separation-marche-client-marche-fournisseur.md`
- integration de cette regle dans `REGLES_METIER_FINANCIERES.md` et `PROJECT_MASTER.md`

## 2026-07-09 - Modele d'objets du Business Engine
- ajout de `docs/decisions/ADR-007-business-engine-domain-model.md`
- ajout de `docs/business/MODELE_OBJETS_BUSINESS_ENGINE.md`
- formalisation des objets `OffreClient`, `CoutLiquidite`, `MargeCible`, `DecisionAcceptation` et `PlanExecution`

## 2026-07-09 - Squelette Python minimal du Business Engine
- ajout du module `engines/business_engine/`
- ajout des objets Python `OffreClient`, `CoutLiquidite`, `MargeCible`, `DecisionAcceptation` et `PlanExecution`
- ajout des composants minimaux `business_engine.py`, `margin_calculator.py`, `liquidity_cost_evaluator.py` et `execution_planner.py`
- ajout des tests unitaires minimaux sur les objets, marges et plans d'execution

## 2026-07-09 - Premier scenario metier XOF -> GNF
- alignement du calcul de marge sur la separation entre offre client et liquidite fournisseur
- choix de la meilleure source de liquidite par marge nette estimee
- ajout d'un premier scenario pur `XOF -> GNF` base sur les cas terrain, sans provider reel ni base de donnees

## 2026-07-09 - Business Engine v0.2
- ajout de `PolitiqueCommerciale` comme cadre metier de decision
- ajout des segments client `standard`, `regulier`, `vip`, `entreprise`
- ajout des decisions `ACCEPTER_AVEC_SURVEILLANCE` et `VALIDATION_MANUELLE_REQUISE`
- ajout des cas simules : client regulier, client VIP, refus automatique et validation manuelle

## 2026-07-10 - Business Engine v0.3
- ajout de `classification_flux`, `volume_mensuel_estime` et `priorite_execution`
- arbitrage explicite entre marge, rapidite, liquidite et relation client
- ajout des sorties de preparation Treasury : `liquidite_consommee`, `reserve_recommandee`, `alerte_liquidite`, `besoin_reapprovisionnement`
- ajout des tests simules : flux ponctuel standard, flux recurrent, flux VIP prioritaire, flux strategique avec reserve recommandee, marge negative refusee et alerte liquidite

## 2026-07-10 - Pont metier Business Engine vers Treasury
- ajout des objets `TresorerieCourante`, `TreasurySnapshot`, `TreasuryRequirement` et `TreasuryAssessment`
- ajout du service `engines/business_engine/treasury_bridge.py` pour exprimer un besoin de tresorerie et evaluer un snapshot simule
- ajout des points d'entree `construire_treasury_requirement` et `evaluer_treasury_snapshot` dans `BusinessEngine`
- ajout des tests simules : liquidite propre suffisante, reserve protegee, recours marchand, recours hybride, liquidite totale insuffisante, flux VIP prioritaire, besoin de reapprovisionnement et isolation multi-devises

## 2026-07-10 - Business Engine v0.4
- ajout de `evaluer_scenario_simule` pour assembler un scenario complet offre client -> Treasury -> decision -> plan d'execution
- maintien de l'independance de l'offre client : aucune re-negociation ni mutation de l'offre acceptee pendant l'optimisation interne
- filtrage des sources selon la recommandation Treasury : `platform`, `merchant`, `provider`, `hybrid`
- ajout des cas simules : liquidite propre suffisante, propre insuffisante avec marchand, mode hybride, changement du plan interne sans changer l'offre, absence de liquidite suffisante, flux VIP recurrent et evolution du taux marchand apres emission de l'offre
- revue rapide de `SPECIFICATION_TECHNIQUE_BUSINESS_ENGINE.md` confirmee : separation marche client / marche fournisseur, reserve minimale, marge negative, explicabilite et priorisation VIP toujours presentes

## 2026-07-10 - Business Engine v0.5
- ajout de `LiquiditySourceDefinition`, `LiquiditySourceState`, `TreasuryDataSource` et `SqlAlchemyLiquidityRepository`
- ajout de `TreasurySnapshotBuilder` pour transformer les soldes reels en `TreasurySnapshot` immuable
- ajout du modele `ExecutionReservation` et de la migration `execution_reservation_foundation`
- ajout de `ExecutionReservationService` pour verrouiller la liquidite via `WalletService` avec revalidation, rollback, idempotence, liberation et expiration
- maintien de la frontiere d'architecture : `BusinessEngine -> PlanExecution -> ExecutionReservationService -> WalletService`
- ajout des tests v0.5 : snapshot multi-sources, reservation platform, reservation merchant, reservation hybride, rollback complet, idempotence, insuffisance apres snapshot, liberation, expiration, reserve minimale, isolation devise et absence de dependance SQLAlchemy dans le Business Engine

## 2026-07-10 - Business Engine v0.6
- ajout de `ConversionOrchestrationService` pour orchestrer une conversion sans execution provider reelle
- ajout des champs de gel d'offre et de snapshots sur `Conversion` avec migration dediee
- branchement de la chaine applicative : `OffreClient -> Business Engine -> TreasurySnapshot -> ExecutionReservationService -> Conversion`
- maintien de l'independance de l'offre client apres acceptation, meme si les couts internes evoluent
- ajout des tests v0.6 : conversion platform, merchant, hybride, VIP, refus avant reservation, insuffisance au verrouillage, rollback post-reservation, idempotence, offre figee, validation manuelle, expiration et annulation

## 2026-07-10 - Business Engine v0.7
- ajout du modele `ConversionExecution` et de la migration associee
- ajout de `ConversionExecutionService` pour faire evoluer une conversion reservee jusqu'a l'execution sans logique provider metier
- ajout des adapters `SimulationExecutionAdapter`, `ManualExecutionAdapter` et `ProviderExecutionAdapter`
- maintien de la separation stricte : `ConversionOrchestrationService -> ConversionExecutionService -> ExecutionAdapter -> ProviderRegistry`
- ajout des tests v0.7 : execution simulee complete, echec payin, echec payout apres payin, pending verification, reprise idempotente, double confirmation, mode manuel, execution interdite sans reservation, offre client figee, conversion terminee non reexecutee, annulation, revue manuelle et tracabilite complete

## 2026-07-11 - Profitability Engine v0.1
- ajout du module `engines/profitability_engine/`
- ajout des objets `ProfitabilityInput` et `ProfitabilityResult`
- ajout des niveaux de rentabilite `perte`, `critique`, `faible`, `acceptable`, `bonne`, `excellente`
- ajout du calcul des couts reels, marge nette reelle, ecart prevision / reel et taux de marge nette
- ajout des tests v0.1 : mode platform, marchand, hybride, marge inferieure, marge superieure, perte, resultat provisoire, couts non recuperables, VIP faible marge et isolation stricte

## 2026-07-11 - EPIC 8.9 Reporting Engine v0.1
- ajout du module `engines/reporting_engine/` pour agreger les KPI par corridor, marchand, client, devise et mode d'execution
- ajout du service applicatif `services/reporting_service.py` pour transformer `Conversion` et `ConversionExecution` en lignes de reporting
- branchement du `Reporting Engine` au `Profitability Engine` pour estimer la marge nette reelle a partir des donnees disponibles
- ajout des tests `test_reporting_engine.py` et `test_reporting_service.py`

## 2026-07-11 - EPIC 8.9 Reporting Admin v0.1
- ajout de la route read-only `/admin/reporting`
- ajout du template `admin_reporting.html` avec filtres par periode, corridor, devise, marchand, mode d'execution et statut
- ajout des agregats read-only par segment client et des vues de supervision : pertes, transactions sous prevision, provisoires vs definitives
- ajout des tests `test_admin_reporting_route.py`
