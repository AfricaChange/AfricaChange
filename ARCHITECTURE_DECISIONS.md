# Architecture Decisions

## AD-001 - Architecture modulaire par domaine
Decision :
- les nouvelles briques scalables doivent etre introduites comme modules dedies
- `providers/`, `engines/` et `webhooks/` sont des points d'entree obligatoires pour les nouveaux developpements structurants

Raison :
- reduire le couplage
- faciliter l'ajout de pays et fournisseurs
- permettre des tests plus cibles

## AD-002 - Le coeur ne depend pas d'un fournisseur
Decision :
- les routes et services applicatifs ne parlent jamais directement a un fournisseur concret
- ils passent par une interface provider commune

Raison :
- permettre le remplacement ou l'ajout d'un fournisseur sans reecriture du coeur

## AD-003 - Webhooks centralises
Decision :
- la verification, l'enregistrement et le dispatch des webhooks doivent etre centralises dans un engine dedie

Raison :
- coherence de securite
- idempotence
- tracabilite

## AD-004 - Engines explicites pour les calculs critiques
Decision :
- pricing, liquidite et rapprochement deviennent des engines independants

Raison :
- encapsuler les regles metier critiques
- faciliter les tests
- preparer le scale

## AD-005 - Documentation obligatoire a la racine
Decision :
- `PROJECT_MASTER.md`, `ARCHITECTURE_DECISIONS.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `ROADMAP.md` doivent exister a la racine et rester a jour

Raison :
- donner un cadre stable a l'equipe
- eviter les evolutions implicites

## AD-006 - Decimal obligatoire pour les nouvelles tables financieres
Decision :
- toutes les nouvelles tables financieres doivent utiliser `Decimal` au niveau applicatif et `NUMERIC` en base
- les tables historiques en `Float` pourront etre migrees progressivement

Raison :
- eviter les erreurs d'arrondi cumulatives
- aligner le modele de donnees avec les exigences fintech

## AD-007 - Registre multi-devises explicite
Decision :
- les devises ne doivent plus etre seulement des strings dispersees
- un modele `Currency` central doit exister pour la validation et la configuration
- les wallets multi-devises doivent etre modelises par devise

Raison :
- preparer l'ajout de pays et devises
- centraliser les regles de precision et d'activation

## AD-008 - Architecture commune de wallets
Decision :
- les wallets doivent converger vers une abstraction commune
- les variantes prevues sont `MerchantWallet`, `PlatformWallet`, `ProviderWallet` et `CustomerWallet`

Raison :
- mutualiser les regles de mutation
- preparer les usages futurs sans refonte du coeur

## AD-009 - Mutations financieres transactionnelles
Decision :
- aucune mutation de wallet ne doit ecrire directement sans orchestrateur transactionnel
- les operations doivent passer par un manager de transaction wallet

Raison :
- garantir l'atomicite entre wallet, registre, audit et effets secondaires

## AD-010 - Separation stricte du Provider Adapter
Decision :
- un provider adapter transforme et adapte
- il ne doit contenir aucune logique metier AfricaChangeX

Raison :
- garder le coeur maitre de ses regles
- remplacer facilement un fournisseur

## AD-011 - Revue d'architecture obligatoire avant implementation
Decision :
- aucun developpement structurant ne commence sans specification, revue d'architecture et validation formelle

Raison :
- eviter le developpement au hasard
- garder une architecture coherente dans le temps

## AD-012 - Architecture en couches : Core, Business, Interfaces
Decision :
- tout ce qui manipule de l'argent doit vivre dans le Core
- la couche Business orchestre les cas d'usage metier
- les Interfaces ne modifient jamais directement un solde

Raison :
- isoler le coeur financier
- permettre le remplacement des interfaces sans refonte metier
- preparer l'ouverture future a d'autres applications et APIs

## AD-013 - Pilotage par domaines metier
Decision :
- le produit est structure par domaines metier explicites
- chaque domaine doit avoir ses propres regles, frontieres et modules

Raison :
- reduire le chaos fonctionnel
- permettre au produit de croitre sans se re-melanger

## AD-014 - Cycle de vie obligatoire des EPIC
Decision :
- chaque EPIC doit suivre un cycle de vie standardise
- ce cycle couvre l'ouverture, le developpement, la revue d'architecture, la cloture et la fusion Git
- aucun EPIC n'est considere termine sans PR, validation et mise a jour documentaire minimale

Raison :
- rendre la gouvernance reproductible
- conserver un historique comprensible des decisions et des livraisons
- aligner code, architecture, documentation et Git

## AD-015 - EPIC de stabilisation periodique
Decision :
- tous les 5 EPIC, un EPIC de stabilisation doit etre planifie
- ces EPIC n'introduisent aucune nouvelle fonctionnalite metier
- ils sont reserves a la dette technique, aux tests, a la documentation, a la securite et a la performance

Raison :
- eviter l'accumulation de dette technique
- stabiliser la plateforme avant les prochaines phases de croissance
- proteger la qualite de l'architecture sur le long terme

## AD-016 - Gel du coeur financier
Decision :
- `Wallet`, `Ledger`, `Settlement`, `MerchantBalance` et `WalletService` sont consideres comme composants du Core financier
- toute modification structurante de ces composants exige une ADR et une revue d'architecture avant implementation

Raison :
- reduire le risque de regression sur les composants les plus sensibles
- traiter le coeur financier comme un actif critique de la plateforme
- forcer un niveau de revue proportionnel au risque

## AD-017 - Ouverture officielle de l'EPIC 8.6
Decision :
- avant l'EPIC 9, AfricaChangeX ouvre officiellement l'EPIC 8.6 `Repository Cleanup & Technical Debt Reduction`
- cet EPIC est non fonctionnel et ne doit modifier aucun comportement produit
- sa sortie attendue inclut un audit de dette technique, un plan legacy et un nettoyage du depot

Raison :
- consolider la base technique avant les prochains EPIC financiers
- reduire la dette pendant que le projet est encore jeune
- preparer une meilleure maintenabilite pour Treasury, Pricing et Provider Integration

## AD-018 - Reservation transactionnelle separee du Business Engine
Decision :
- le `Business Engine` ne lit ni ne modifie directement les soldes reels
- les soldes reels sont transformes en `TreasurySnapshot` via un builder dedie
- toute reservation reelle passe par `ExecutionReservationService`
- toute mutation effective continue de passer par `WalletService`

Raison :
- proteger la separation entre decision metier et mutation comptable
- revalider la liquidite au moment du lock
- garantir l'idempotence, le rollback et les traces d'audit avant toute execution fournisseur reelle

## AD-019 - La conversion orchestre, le provider execute plus tard
Decision :
- la conversion devient le premier cas d'usage applicatif complet au-dessus du `Business Engine`
- le checkout, le payin et le payout provider ne pilotent pas la conversion
- `ConversionOrchestrationService` fige l'offre, evalue, reserve et prepare la conversion avant toute execution externe

Raison :
- garder le metier maitre du parcours principal
- eviter qu'un moyen d'encaissement dicte la logique de conversion
- preparer un branchement provider ulterieur sans casser la chaine metier

## AD-020 - L'execution externe passe par un adapter controle
Decision :
- toute conversion reservee passe par `ConversionExecutionService`
- le mode d'execution est choisi entre `simulation`, `manuel` et `api`
- le mode `api` utilise un adapter provider abstrait et non une logique SenePay directe

Raison :
- proteger le coeur metier contre la variabilite des providers
- valider les etats d'execution avant tout branchement fournisseur reel
- permettre une execution simulee et manuelle sans bloquer le parcours global
