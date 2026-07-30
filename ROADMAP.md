# Roadmap

## Maintenant
- stabiliser l'architecture modulaire
- standardiser les providers
- centraliser les webhooks
- isoler les engines critiques
- preparer le treasury engine
- cadrer l'EPIC 9 - Treasury Intelligence
- preparer les premiers EPIC metier centres sur le corridor Senegal <-> Guinee

## Ensuite
- brancher progressivement les flux existants sur `providers/`
- modulariser le modele de donnees si la taille continue de croitre
- ajouter le rapprochement fournisseur / ledger / mobile money
- introduire un event store interne
- isoler progressivement `core/ledger`, `core/wallet`, `core/settlement`
- lancer l'EPIC 9 - Treasury Intelligence
- lancer l'EPIC 10 - Pricing Engine
- lancer l'EPIC 11 - Integration SenePay
- lancer l'EPIC 12 - Reconciliation
- lancer l'EPIC 13 - Pilote Senegal <-> Guinee

## Plus tard
- multi-pays complet
- multi-aggregateurs actifs
- supervision temps reel
- reporting conformite et finance avance
- applications multi-interface autour d'un coeur financier unique

## Cadence de stabilisation
- apres chaque bloc de 5 EPIC, un EPIC de stabilisation doit etre planifie
- ces EPIC sont reserves au nettoyage, a la dette technique, a la qualite, aux tests, a la documentation et a la securite

## Jalon actuel
- `Fintech Foundation v0.9` atteint
- le projet peut entrer dans les EPIC metier apres cadrage de Treasury
