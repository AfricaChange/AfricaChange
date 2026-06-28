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

## Principes produit
- Le coeur metier ne depend jamais directement d'un fournisseur.
- Toute integration externe passe par une interface commune.
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

## Regles d'evolution
- Toute nouvelle integration fournisseur doit entrer dans `providers/`.
- Toute nouvelle logique de calcul doit entrer dans `engines/`.
- Toute nouvelle logique de reception fournisseur doit entrer dans `webhooks/`.
- Toute decision d'architecture doit etre ajoutee a `ARCHITECTURE_DECISIONS.md`.
- Toute evolution notable doit etre notee dans `CHANGELOG.md` et `ROADMAP.md`.
- Aucun module financier critique ne commence sans specification validee.
- Toute evolution d'EPIC doit etre relue et consignee dans `docs/architecture/ARCHITECT_REVIEW.md`.
