# Specification Technique - Business Engine

## Objectif

Definir le cadre technique du `Business Engine` d'AfricaChangeX.

Ce module ne parle ni directement aux providers, ni a Flask, ni a la base de donnees.

Son role est de transformer une demande client et des informations de liquidite en decision metier explicable.

## Role du Module

Le `Business Engine` doit :

- recevoir une offre client deja definie ;
- evaluer le cout de liquidite disponible ;
- appliquer la politique commerciale ;
- produire une decision d'acceptation ;
- proposer un plan d'execution ;
- exprimer un besoin de tresorerie vers le futur Treasury Intelligence.

Il ne doit pas :

- calculer seul le prix affiche au client ;
- appeler directement SenePay ou un autre fournisseur ;
- modifier un wallet ou un solde reel ;
- executer une ecriture comptable.

## Position dans l'Architecture

Le flux cible est :

`Demande client -> OffreClient -> TreasuryRequirement -> TreasurySnapshot -> TreasuryAssessment -> CoutLiquidite -> DecisionAcceptation -> PlanExecution`

Le `Business Engine` reste un domaine autonome.

## Entrees du Module

Les entrees principales sont :

- `OffreClient`
- `CoutLiquidite`
- `MargeCible`
- `PolitiqueCommerciale`
- `TreasurySnapshot`

### Entree 1 - OffreClient

Expose le contrat visible par le client :

- montant source ;
- devise source ;
- montant destination ;
- devise destination ;
- taux client ;
- frais client ;
- delai annonce ;
- segment client ;
- classification du flux ;
- volume mensuel estime ;
- priorite d'execution.

### Entree 2 - CoutLiquidite

Expose le cout interne d'execution :

- source de liquidite ;
- type de source ;
- cout reel destination ;
- frais d'execution ;
- cout operationnel ;
- delai d'execution ;
- niveau de risque ;
- liquidite disponible.

### Entree 3 - PolitiqueCommerciale

Cadre metier configurable du moteur :

- marge minimale ;
- priorite rapidite ;
- autorisation de tresorerie interne ;
- autorisation du mode hybride ;
- reserve minimale ;
- seuil d'alerte liquidite ;
- regles de validation manuelle ;
- regles de surveillance.

### Entree 4 - TreasurySnapshot

Vue normalisee de la tresorerie :

- capacite propre mobilisable ;
- capacite externe mobilisable ;
- capacite totale mobilisable ;
- reserve de securite ;
- alerte ;
- besoin de reapprovisionnement ;
- ventilation marchand / fournisseur.

## Sorties du Module

Le moteur doit produire :

- `DecisionAcceptation`
- `PlanExecution`
- `TreasuryRequirement`
- `TreasuryAssessment`

### Sortie 1 - DecisionAcceptation

Resultat metier principal :

- code de decision ;
- motif principal ;
- marge estimee ;
- delai estime ;
- source de liquidite recommandee ;
- validation manuelle requise ou non ;
- niveau d'alerte liquidite ;
- besoin de reapprovisionnement.

### Sortie 2 - PlanExecution

Plan concret d'execution :

- source de liquidite ;
- mode d'execution ;
- priorite ;
- cout estime ;
- marge estimee ;
- delai estime ;
- strategie de fallback.

### Sortie 3 - TreasuryRequirement

Besoin exprime par le Business Engine :

- montant cible ;
- devise cible ;
- delai maximal ;
- priorite d'execution ;
- classification du flux ;
- segment client ;
- reserve a preserver.

### Sortie 4 - TreasuryAssessment

Recommandation tresorerie :

- liquidite suffisante ;
- source recommandee ;
- montant propre utilisable ;
- montant externe necessaire ;
- mode recommande ;
- niveau d'alerte ;
- justification ;
- besoin de reapprovisionnement.

## Etats de Decision

Les etats minimums a supporter sont :

- `ACCEPTER`
- `ACCEPTER_AVEC_MARGE_REDUITE`
- `ACCEPTER_AVEC_SURVEILLANCE`
- `ACCEPTER_EN_MODE_HYBRIDE`
- `VALIDATION_MANUELLE_REQUISE`
- `REFUSER_PAR_MANQUE_DE_LIQUIDITE`
- `REFUSER_PAR_MARGE_NEGATIVE`

## Etapes de Decision

Le moteur suit la sequence suivante :

1. recevoir `OffreClient` ;
2. exprimer un `TreasuryRequirement` ;
3. consommer un `TreasurySnapshot` ;
4. produire un `TreasuryAssessment` ;
5. evaluer les `CoutLiquidite` disponibles ;
6. calculer la marge nette ;
7. appliquer la `PolitiqueCommerciale` ;
8. rendre une `DecisionAcceptation` ;
9. produire un `PlanExecution`.

## Regles Metier a Implementer

Les regles a respecter sont :

- separation entre marche client et marche fournisseur ;
- priorite a la marge nette, sauf arbitrage explicite ;
- possibilite de marge reduite pour client regulier, VIP ou flux strategique ;
- protection de la reserve minimale ;
- refus si la marge nette est negative ;
- recours marchand si la capacite propre est insuffisante ;
- recours fournisseur si la capacite marchand est insuffisante ;
- recours hybride si plusieurs sources sont necessaires ;
- validation manuelle pour certains nouveaux clients a risque ;
- surveillance pour risque moyen ou eleve ;
- preservation de la qualite de service client.

## Objets Metier a Prevoir

Le domaine contient au minimum :

- `OffreClient`
- `CoutLiquidite`
- `MargeCible`
- `PolitiqueCommerciale`
- `DecisionAcceptation`
- `PlanExecution`
- `TresorerieCourante`
- `TreasurySnapshot`
- `TreasuryRequirement`
- `TreasuryAssessment`

## Services a Prevoir

Les services minimums du domaine sont :

- `BusinessEngine`
- `MarginCalculator`
- `LiquidityCostEvaluator`
- `ExecutionPlanner`
- `TreasuryBridge`

## Dependances Metier Autorisees

Le module peut dependre :

- des enums du domaine ;
- des objets metier du domaine ;
- de contrats entrants normalises.

Le module ne doit pas dependre :

- d'un provider concret ;
- d'une route Flask ;
- d'un modele SQLAlchemy ;
- d'un wallet reel ;
- d'un webhook concret.

## Extension Reporting Engine

Le `Reporting Engine` vient apres l'execution et la rentabilite.

Son role est de transformer les donnees produites par :

- `Conversion` ;
- `ConversionExecution` ;
- `Business Engine` ;
- `Profitability Engine` ;
- les snapshots de tresorerie et de reservation disponibles ;

en indicateurs lisibles pour le pilotage.

Les dimensions minimales a supporter sont :

- corridor ;
- marchand ;
- client ;
- devise ;
- mode d'execution.

Le tableau de bord admin read-only peut ensuite consommer ces agregats pour exposer :

- la marge nette par corridor ;
- la marge nette par devise ;
- la repartition par mode `platform`, `merchant`, `hybrid`, `provider` ;
- la rentabilite par marchand ;
- la rentabilite par segment client ;
- les transactions en perte ;
- les transactions sous prevision ;
- les conversions provisoires ou non finalisees.

Le `Reporting Engine` reste lui aussi un module pur :

- pas d'appel provider ;
- pas d'import Flask ;
- pas d'acces SQLAlchemy dans le moteur pur ;
- pas de mutation de solde ;
- agregation read-only uniquement.

## Cas de Test a Prevoir

Les cas minimums sont :

- creation d'une offre client ;
- calcul de marge brute ;
- refus sur marge negative ;
- execution avec liquidite propre ;
- execution avec marchand ;
- execution hybride ;
- flux ponctuel standard ;
- flux recurrent avec marge reduite ;
- flux VIP prioritaire ;
- validation manuelle ;
- surveillance ;
- liquidite propre suffisante ;
- reserve minimale protegee ;
- recours marchand si propre insuffisante ;
- liquidite totale insuffisante ;
- besoin de reapprovisionnement ;
- isolation multi-devises.

## Journalisation et Audit

Chaque decision doit rester explicable.

Il faut conserver au minimum :

- l'offre client ;
- les couts de liquidite utilises ;
- le snapshot de tresorerie consomme ;
- la decision rendue ;
- la justification ;
- le plan d'execution ;
- les alertes et besoins de reapprovisionnement.

## Criteres de Validation

Le module est valide si :

- les montants utilisent `Decimal` ;
- les dependances restent propres ;
- la logique metier est testee ;
- les sorties sont explicables ;
- les contrats Treasury restent simules ;
- aucun acces direct aux soldes reels n'apparait.

## Conclusion

Cette specification definit une version technique stable du `Business Engine` avant branchement vers le futur Treasury Intelligence reel.

La prochaine etape n'est pas encore EPIC 9 complet.

Elle consiste uniquement a maintenir une frontiere propre :

`Business Engine -> TreasuryRequirement -> TreasurySnapshot -> TreasuryAssessment -> PlanExecution`

## Extension v0.4 - Simulation contractuelle complete

La version v0.4 assemble maintenant un scenario complet en simulation :

`Demande client -> OffreClient -> PolitiqueCommerciale -> TreasuryRequirement -> TreasuryAssessment -> DecisionAcceptation -> PlanExecution`

Regles confirmees :

- l'offre client reste figee pendant sa duree de validite ;
- l'optimisation interne peut changer le plan d'execution, jamais le contrat deja accepte par le client ;
- le mode d'execution peut etre `platform`, `merchant`, `provider` ou `hybrid` ;
- l'absence de liquidite suffisante conduit a une validation manuelle ou a un refus selon la politique ;
- les flux VIP et strategiques peuvent accepter une marge plus faible sans violer la reserve minimale.

## Extension v0.5 - Pont transactionnel vers les soldes reels

La version v0.5 ne donne toujours pas au `Business Engine` un acces direct aux wallets.

La chaine cible devient :

`LiquidityRepository -> TreasurySnapshotBuilder -> TreasurySnapshot -> Business Engine -> DecisionAcceptation + PlanExecution -> ExecutionReservationService -> WalletService`

Regles obligatoires :

- le snapshot reste immuable pendant l'evaluation ;
- une decision du `Business Engine` n'est pas une garantie de reservation ;
- la liquidite est revalidee au moment du verrouillage ;
- si la liquidite a change, la reservation echoue proprement ou demande une nouvelle evaluation ;
- aucune mutation n'est faite par le `Business Engine` ;
- toute mutation passe par `WalletService` ;
- toute reservation genere `WalletEntry` et `AuditLog` ;
- l'idempotence est garantie par `transaction_reference` ;
- aucune execution provider reelle n'entre encore dans ce perimetre ;
- l'offre client n'est jamais modifiee apres acceptation.

Composants techniques ajoutes :

- `services/liquidity_repository.py`
- `services/treasury_snapshot_builder.py`
- `services/execution_reservation_service.py`
- `models.ExecutionReservation`

Cas de test cibles confirmes :

- construction de snapshot depuis balances reelles simulees ;
- reservation platform ;
- reservation merchant ;
- reservation hybride atomique ;
- rollback complet en cas d'echec partiel ;
- idempotence sur double appel ;
- liquidite devenue insuffisante entre snapshot et reservation ;
- liberation apres echec ;
- expiration ;
- protection de la reserve minimale ;
- isolation stricte par devise ;
- absence de dependance SQLAlchemy / WalletService dans le `Business Engine`.

## Extension v0.6 - Orchestration d'une conversion

La version v0.6 introduit un cas d'usage applicatif au-dessus du `Business Engine` sans appeler encore de provider reel.

Chaine cible :

`Demande de conversion -> OffreClient -> Business Engine -> TreasurySnapshot -> ExecutionReservationService -> Conversion`

Service ajoute :

- `services/conversion_orchestration_service.py`

Responsabilites :

- creer une offre client figee ;
- accepter l'offre ;
- construire les couts de liquidite disponibles ;
- construire le snapshot Treasury reel ;
- evaluer la decision et le plan ;
- reserver la liquidite si possible ;
- persister la conversion avec ses snapshots et references ;
- ne declencher aucun payin ni payout provider.

Regles obligatoires :

- l'offre client ne change plus apres acceptation ;
- la reservation echouee ne modifie pas l'offre client ;
- aucun provider reel n'est appele ;
- toute erreur libere ou annule proprement la reservation ;
- la reference de conversion relie offre, decision, plan, reservation, wallet entries et audit.

Cas de test v0.6 :

- conversion platform ;
- conversion merchant ;
- conversion hybride ;
- client VIP avec marge reduite ;
- refus sur marge negative ;
- insuffisance au verrouillage ;
- rollback complet si l'etape post-reservation echoue ;
- idempotence ;
- offre client figee ;
- validation manuelle ;
- expiration de quote ;
- annulation avec liberation.

## Extension v0.7 - Orchestration d'execution controlee

La version v0.7 fait evoluer une conversion reservee jusqu'a son execution sans laisser un provider externe piloter le metier.

Architecture cible :

`ConversionOrchestrationService -> ConversionExecutionService -> ExecutionAdapter -> ProviderRegistry -> provider`

Composants ajoutes :

- `models.ConversionExecution`
- `services/execution_adapters.py`
- `services/conversion_execution_service.py`

Modes supportes :

- `simulation`
- `manuel`
- `api`

Regles obligatoires :

- aucun appel provider direct dans les routes ;
- aucun recalcul du pricing dans le service d'execution ;
- `pending_verification` n'est pas un echec ;
- un payin confirme n'est jamais credite deux fois ;
- un payout echoue apres payin confirme bascule en revue manuelle ;
- une conversion `completed` n'est plus reexecutee ;
- l'idempotence reutilise la meme reference d'execution ;
- le mode `api` peut rester desactive tant que le fournisseur n'est pas valide.

Cas de test v0.7 :

- execution simulee complete ;
- payin simule echoue ;
- payout echoue apres payin ;
- payout en `pending_verification` ;
- reprise apres timeout ;
- double confirmation sans double mouvement ;
- mode manuel avec preuve ;
- execution interdite sans reservation ;
- offre client non modifiee ;
- conversion deja terminee non reexecutee ;
- annulation avant payin ;
- echec apres payin avec revue manuelle ;
- separation stricte avec SenePay ;
- tracabilite complete conversion -> reservation -> execution -> wallet -> audit.
