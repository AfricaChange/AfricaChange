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
