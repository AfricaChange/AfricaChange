# Roadmap

## Maintenant
- stabiliser l'architecture modulaire
- standardiser les providers
- centraliser les webhooks
- isoler les engines critiques
- preparer l'EPIC 8 - registre multi-monnaies
- preparer le treasury engine
- cadrer l'EPIC 9 - Core financier

## Ensuite
- brancher progressivement les flux existants sur `providers/`
- introduire de vraies balances par devise pour les marchands
- modulariser le modele de donnees si la taille continue de croitre
- ajouter le rapprochement fournisseur / ledger / mobile money
- introduire une table `Currency`
- introduire un event store interne
- isoler progressivement `core/ledger`, `core/wallet`, `core/settlement`

## Plus tard
- multi-pays complet
- multi-aggregateurs actifs
- supervision temps reel
- reporting conformite et finance avance
- applications multi-interface autour d'un coeur financier unique
