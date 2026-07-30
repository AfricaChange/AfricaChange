# AfricaChangeX - Project Master

## Vision
Vision Produit :
AfricaChangeX est une infrastructure panafricaine d'orchestration des paiements, de la liquidite et de la conversion de devises. Sa mission est de connecter les differents moyens de paiement africains au sein d'une plateforme unique, securisee, conforme et evolutive.

Le systeme doit supporter :
- plusieurs agregateurs de paiement
- plusieurs pays
- plusieurs devises
- liquidite interne + liquidite marchands
- controles de risque, litiges, rapprochement et comptabilite interne
- une separation claire entre coeur financier, logique metier et interfaces

## Gouvernance produit
Le produit est desormais pilote par EPIC, pas par fonctionnalite isolee.
AfricaChangeX entre officiellement en `Phase 2 - Infrastructure Fintech`.

Phases produit :
- Phase 1 - Fondations
- Phase 2 - Infrastructure Fintech
- Phase 3 - Pilote Senegal ↔ Guinee
- Phase 4 - Expansion CEDEAO
- Phase 5 - Infrastructure panafricaine

Etat de reference :
- EPIC 1 - Infrastructures : termine
- EPIC 2 - Conformite : termine
- EPIC 3 - SenePay : en cours
- EPIC 4 - Moteur de tarification : a faire
- EPIC 5 - Moteur de liquidite : a faire
- EPIC 6 - Marche des marchands : a faire
- EPIC 7 - Moteur de reglement : partiellement termine
- EPIC 8 - Registre multi-monnaies : termine
- EPIC 8.5 - Wallet Administration : termine
- EPIC 8.6 - Repository Cleanup & Technical Debt Reduction : termine
- EPIC 9 - Treasury Intelligence : a cadrer
- EPIC 10 - Moteur de tarification : a cadrer
- EPIC 11 - Provider Integration : a cadrer
- EPIC 12 - Pilote Senegal <-> Guinee : a cadrer

Cycle obligatoire :
- idee
- specification
- revue d'architecture
- validation
- codage
- tests
- documentation
- fusion

Cycle de vie obligatoire d'un EPIC :
1. ouverture de l'EPIC
- objectifs
- perimetre
- hors perimetre
- criteres de validation
- risques
2. developpement
- code
- tests
- documentation
3. revue d'architecture
- validation
- observations
- dette technique creee
- dette technique supprimee
4. cloture
- mise a jour de `CHANGELOG.md`
- mise a jour de `PROJECT_MASTER.md`
- mise a jour de `ROADMAP.md`
5. fusion Git
- PR validee
- fusion
- tag si necessaire

## Principes produit
- Le coeur metier ne depend jamais directement d'un fournisseur.
- Toute integration externe passe par une interface commune.
- Le marche client et le marche fournisseur sont separes ; le client contracte avec AfricaChangeX, pas avec le marchand.
- Les routes HTTP restent fines ; la logique vit dans les services et moteurs.
- Toute donnee financiere doit etre traçable dans le ledger.
- Toute nouvelle brique doit etre pensee pour le scale regional.
- Toute nouvelle table financiere doit utiliser `Decimal` / `NUMERIC`.
- Les soldes multi-devises doivent etre modelises explicitement.
- Les providers adaptent seulement des APIs ; ils ne portent aucune logique metier.
- Tout ce qui manipule de l'argent doit vivre dans le Core.
- Les interfaces ne doivent jamais modifier directement un solde.

## Architecture cible a long terme
- `core/`
- `core/ledger/`
- `core/wallet/`
- `core/treasury/`
- `core/pricing/`
- `core/settlement/`
- `core/reconciliation/`
- `providers/`
- `apps/web/`
- `apps/admin/`
- `apps/merchant/`
- `apps/mobile/`

Principe :
- le Core manipule l'argent
- la couche metier orchestre les cas d'usage
- les interfaces exposent le produit sans porter le coeur financier

## Domaines metier
- Identite : authentification, KYC
- Tresor : wallet, soldes marchands, liquidite
- Paiements : payin, payout, QR
- FX : conversion, taux, pricing
- Conformite : AML, surveillance, risque
- Fournisseurs : SenePay, CinetPay, Orange, MTN
- Reporting : dashboards, KPI, audit

## Modele economique
Principe fondateur :
AfricaChangeX n'est pas remuneree parce qu'elle "fait un change". Elle est remuneree parce qu'elle orchestre un reseau de paiement et de liquidite.

Sources de revenus cibles :
- marge de change
- commission de service
- services marchands
- optimisation de liquidite
- services premium a terme

## Modules cibles
- `providers/` : integrations fournisseurs et registre commun
- `engines/` : pricing, liquidite, rapprochement
- `engines/treasury_engine.py` : surveillance et pilotage de tresorerie
- `webhooks/` : reception et orchestration des webhooks
- `services/` : orchestration metier transverse
- `services/merchant_wallet_admin_service.py` : operations admin sur wallets marchands avec audit
- `routes/` : exposition HTTP / admin / API
- `docs/architecture/ARCHITECT_REVIEW.md` : revue formelle par EPIC
- `models.py` : modele de donnees actuel, a modulariser progressivement si la taille continue de croitre

## Priorites techniques en cours
1. architecture multi-aggregateurs
2. adapter provider commun
3. webhook engine securise
4. pricing engine independant du fournisseur
5. liquidity engine multi-sources
6. reconciliation engine
7. dashboards et supervision
8. registre multi-monnaies
9. wallet administration
10. treasury engine
11. event store interne
12. core financier

## Reserve operationnelle active

Tant que `conversion.statut` reste en `VARCHAR(20)` sur Render, aucun parcours deploye ne doit tenter d'enregistrer `manual_review_required` ou tout autre statut long.

La migration corrective d'elargissement reste une dette prioritaire avant activation operationnelle reelle du mode manuel et des futurs etats longs.

## EPIC officiellement ouvert
### EPIC 8.6 - Repository Cleanup & Technical Debt Reduction

Objectifs :
- reduire la dette technique
- identifier les elements legacy
- supprimer le code mort
- uniformiser l'architecture
- preparer le projet pour les futurs EPIC

Perimetre :
- audit du depot
- identification du code obsolete, duplique ou inutilise
- nettoyage des fichiers temporaires, generes et oublies
- identification des usages SQLAlchemy 2.x deprecies
- verification de coherence entre code, documentation et structure du projet

Hors perimetre :
- aucune nouvelle fonctionnalite produit
- aucune refonte comportementale
- aucune migration lourde hors dette technique explicitement documentee

Criteres de validation :
- un rapport `docs/architecture/TECH_DEBT.md`
- la liste des suppressions effectuees
- la liste des elements legacy conserves
- la liste des recommandations structurelles
- les tests executes
- une estimation de la dette technique restante

Risques :
- suppression accidentelle d'un element encore utilise
- confusion entre legacy temporaire et code mort reel
- elargissement du nettoyage au-dela d'un perimetre non fonctionnel

### EPIC SenePay Sandbox - Phase 1

Objectif :
- connecter AfricaChangeX au provider SenePay Sandbox via l'architecture Provider Adapter existante

Perimetre :
- appels techniques Sandbox SenePay
- service interne de test Sandbox
- page admin de test technique
- journaux et audits des tests Sandbox
- tests unitaires mock HTTP

Contraintes :
- aucune logique metier AfricaChangeX dans le provider
- aucune dependance directe du Business Engine a SenePay
- aucun secret commite
- variables SenePay uniquement via `.env`

Hors perimetre :
- aucun branchement du Business Engine
- aucune logique de pricing ou de decision metier
- aucun webhook metier complet
- aucune mise en production SenePay

Critere de validation :
- le provider SenePay Sandbox repond via l'adapter commun
- la page admin `/admin/senepay-sandbox` permet de tester les endpoints cibles
- les journaux techniques permettent de suivre requete, reponse, statut et reference interne
- les tests automatises n'appellent pas reellement SenePay

### EPIC 9.0.2 - MerchantExecutionAdapter

Objectif :
- permettre a AfricaChangeX de confier tout ou partie de l'execution interne d'une conversion a un marchand sans exposer ce marchand au client et sans modifier l'offre client deja acceptee

Perimetre de cette phase :
- specification officielle en francais
- machine d'etats
- objets metier
- regles de reaffectation
- scenarios de reference
- KPI marchands

Hors perimetre :
- PostgreSQL local
- restauration de sauvegarde
- dette Alembic historique
- application de la migration corrective sur Render
- integration SenePay
- ecriture du code du MerchantExecutionAdapter

Critere de validation :
- specification `docs/business/EPIC_9_0_2_MERCHANT_EXECUTION_ADAPTER.md` approuvee
- responsabilites du MerchantExecutionAdapter stabilisees
- machine d'etats documentee
- scenarios de reaffectation documentes
- KPI marchands definis

Risque :
- confusion entre marche client et marche marchand
- double reservation de liquidite
- reaffectation tardive
- fuite d'identite marchand cote client

## Regles de stabilisation
- tous les 5 EPIC, un EPIC de stabilisation doit etre planifie
- pendant un EPIC de stabilisation, aucune nouvelle fonctionnalite n'est ajoutee
- le travail porte uniquement sur la dette technique, les tests, la documentation, la securite et la robustesse

## Categories d'EPIC

EPIC d'infrastructure :
- gouvernance
- wallets
- nettoyage du depot
- cadre providers
- core
- qualite et tests

EPIC metier :
- treasury
- pricing
- conversion intelligente
- paiements QR
- SenePay
- pilote Senegal <-> Guinee

Regle produit :
- a partir d'EPIC 9, chaque EPIC metier doit contribuer directement a la capacite de realiser un paiement ou une conversion reelle entre deux pays africains

## Regles de gel du Core
- `Wallet`, `Ledger`, `Settlement`, `MerchantBalance` et `WalletService` sont des composants du coeur financier
- toute modification structurante de ce coeur exige une ADR et une revue d'architecture formelle avant implementation

## Regles d'evolution
- Toute nouvelle integration fournisseur doit entrer dans `providers/`.
- Toute nouvelle logique de calcul doit entrer dans `engines/`.
- Toute nouvelle logique de reception fournisseur doit entrer dans `webhooks/`.
- Toute decision d'architecture doit etre ajoutee a `ARCHITECTURE_DECISIONS.md`.
- Toute evolution notable doit etre notee dans `CHANGELOG.md` et `ROADMAP.md`.
- Aucun module financier critique ne commence sans specification validee.
- Toute evolution d'EPIC doit etre relue et consignee dans `docs/architecture/ARCHITECT_REVIEW.md`.

## Referentiel valide

Le dossier `docs/referentiel/` est desormais considere comme la source officielle de connaissance d'AfricaChangeX.

Le referentiel valide v1.0 comprend notamment :

- la charte du referentiel
- le cycle de vie d'un EPIC
- la matrice de tracabilite
- les documents de gouvernance
- les documents metier
- les documents d'architecture
- les ADR
- les hypotheses metier
- la revue croisee du referentiel

Regles associees :

- toute modification substantielle du referentiel doit etre justifiee dans un `ADR` ou dans le `CHANGELOG`
- aucune regle metier ne doit exister uniquement dans le code
- tout EPIC doit etre coherent avec le Financial Operating Model, les ADR, le Lexique Metier, les Regles Metier, les Scenarios de Reference et les Hypotheses Metier avant fusion
- le referentiel AfricaChangeX v1.0 constitue la base stable avant l'implementation du Business Engine
