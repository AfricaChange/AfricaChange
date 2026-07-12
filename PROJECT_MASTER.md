# AfricaChangeX - Project Master

## Vision

AfricaChangeX est une plateforme de paiement, de conversion et d'orchestration de liquidite.

## Etat de reference

- EPIC 8.9 - Reporting Engine : valide et ferme
- EPIC 9 - Treasury Intelligence : a cadrer
- EPIC 10 - Pricing Engine : a cadrer
- EPIC 11 - Integration SenePay : a cadrer
- EPIC 12 - Reconciliation : a cadrer
- EPIC 13 - Pilote Senegal <-> Guinee : a cadrer

## Decision de cloture EPIC 8.9

Le reporting financier read-only est considere comme valide en version `v1.0`.

Couverture validee :

- conversion rentable
- conversion en perte
- conversion provisoire
- mode `platform`
- mode `merchant`
- mode `hybrid`
- conversion annulee
- conversion rejetee

Garanties d'architecture :

- moteur pur independant de Flask
- moteur pur independant de SQLAlchemy
- aucune ecriture financiere
- aucune dependance provider
- aucune modification des taux client
- dashboard reserve a l'administration
