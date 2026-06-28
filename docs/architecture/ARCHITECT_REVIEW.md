# Architect Review

## Role
Ce document conserve la revue d'architecture officielle par EPIC.

Chaque entree doit contenir :
- la note d'architecture
- les points forts
- les points a ameliorer
- les decisions prises
- les impacts futurs

## EPIC 8 - Registre multi-monnaies

### Note
9.8 / 10

### Points forts
- le besoin produit est correct et structurant
- la direction `Multi-Currency Wallet` est la bonne
- l'integration avec liquidite, pricing, settlement, ledger et dashboard est coherente
- le module est pense pour le scale futur

### Points a ameliorer
- remplacer `Float` par `Decimal` pour les nouvelles tables financieres
- introduire un modele `Currency` central
- generaliser la notion de wallet au-dela du seul marchand
- imposer un `WalletTransactionManager` transactionnel
- enrichir les ecritures avec un `TransactionContext`
- preparer les evenements internes et un futur event store
- ajouter un `Treasury Engine`

### Decisions prises
- toute nouvelle table financiere utilisera `Decimal` / `NUMERIC`
- les providers restent des adapters sans logique metier
- la suite du projet sera pilotee par specification, revue d'architecture et validation
- l'EPIC 8 doit commencer par le module `Multi-Currency Wallet`

### Impacts futurs
- facilite l'ajout de nouvelles devises
- facilite les audits et la conformite
- reduit le risque de refonte lors de l'ajout de nouveaux pays et partenaires
- prepare la tresorerie, le rapprochement et les wallets multi-acteurs

## EPIC 9 - Core financier

### Note
Concept valide

### Points forts
- separe le coeur financier des interfaces
- prepare l'arrivee future de Flutter, React, mobile et API publique
- aligne AfricaChangeX avec une architecture de plateforme

### Points a ameliorer
- definir les frontieres exactes entre `core/`, `engines/` et `services/`
- definir le plan de migration progressif depuis Flask actuel

### Decisions prises
- tout ce qui manipule de l'argent doit vivre dans le Core
- les interfaces ne modifieront jamais directement un solde
- la couche metier devra orchestrer les cas d'usage entre Core et providers

### Impacts futurs
- facilite le scale multi-canal
- diminue le couplage entre produit et technologie d'interface
- rend possible une vraie API publique sans refonte du coeur

## EPIC 8.5 - Wallet Administration

### Note
9.9 / 10

### Points forts
- la logique admin wallet reste dans un service dedie
- l'administration wallet passe par une route et une page dediees
- chaque action cree un `WalletEntry`, un `AuditLog` et un `AdminWalletAction`
- les controles d'acces, de devise, de montant et de motif sont verifies
- l'interface expose un historique exploitable sans lecture directe de la base

### Points a ameliorer
- ajouter a terme une double validation pour les montants critiques
- generaliser la meme logique aux wallets plateforme et provider
- brancher plus tard un event bus interne sur les actions wallet

### Decisions prises
- aucune mutation admin de wallet ne doit contourner `WalletService`
- toute action admin wallet doit laisser une double trace finance + audit
- toute action admin wallet doit avoir une reference et un motif obligatoires
- un seuil configurable impose une confirmation explicite sur montant sensible

### Impacts futurs
- prepare les operations de sandbox, correction, recharge et reconciliation
- reduit le risque d'operations manuelles non tracables
- cree une base reutilisable pour les wallets plateforme et provider
