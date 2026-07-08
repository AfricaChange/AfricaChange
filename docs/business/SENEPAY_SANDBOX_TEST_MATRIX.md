# SenePay Sandbox Test Matrix

## Objet

Ce document recense les scenarios Sandbox qui doivent etre verifies avant toute implementation metier supplementaire.

## Regle

Un scenario n'est considere valide que si :

- le resultat attendu est defini
- l'effet wallet / ledger attendu est defini
- l'effet webhook attendu est defini
- l'idempotence est verifiee si applicable

## Matrice

| ID | Cas | Resultat attendu | Effet financier attendu | Statut |
| --- | --- | --- | --- | --- |
| SBX-001 | Payin succes | transaction confirmee | wallet credite | A faire |
| SBX-002 | Payin refuse | transaction rejetee | aucun credit | A faire |
| SBX-003 | Payin pending | transaction en attente | aucun profit reconnu | A faire |
| SBX-004 | Payout succes | payout finalise | pending -> settled | A faire |
| SBX-005 | Payout echoue | payout rejete | rollback ou reprise conforme | A faire |
| SBX-006 | Webhook recu 2 fois | traitement unique | idempotence respectee | A faire |
| SBX-007 | Webhook reference inconnue | rejet controle | aucune mutation financiere | A faire |
| SBX-008 | Timeout fournisseur | retry conforme | aucun double debit | A faire |
| SBX-009 | Retry manuel | reprise controlee | aucun double effet wallet | A faire |
| SBX-010 | Cle test invalide | erreur auth | aucun effet metier | A faire |
| SBX-011 | Montant invalide | validation rejetee | aucune ecriture | A faire |
| SBX-012 | Devise non supportee | erreur controlee | aucune mutation | A faire |
| SBX-013 | Callback avant polling | webhook prioritaire | etat final coherent | A faire |
| SBX-014 | Polling sans webhook | etat recupere | coherence transactionnelle | A faire |
| SBX-015 | Payout apres reserve payin | couts coherents | marge recalculable | A faire |
| SBX-016 | Reference idempotence repetee | pas de doublon | une seule transaction | A faire |
| SBX-017 | Beneficiaire invalide | payout refuse | aucun settled | A faire |
| SBX-018 | Sandbox Senegal | succes testable | flux SN valide | A faire |
| SBX-019 | Sandbox Guinee | succes testable | flux GN valide | A faire |
| SBX-020 | Scenario complet XOF -> GNF | payin + conversion + payout | profit calculable | A faire |

## Sortie attendue

Avant tout code metier supplementaire, cette matrice doit etre completee avec :

- statut reel
- notes de comportement
- references de tests
- observations sur les ecarts entre documentation et realite

## Phase 1 - Connexion technique provider

Cette phase couvre uniquement la capacite d'AfricaChangeX a parler a SenePay proprement via le provider adapter, sans logique metier.

| ID | Endpoint / test technique | Resultat attendu | Statut |
| --- | --- | --- | --- |
| SBX-P1-001 | `POST /api/v1/checkout/sessions` | session checkout creee et reponse normalisee | A faire |
| SBX-P1-002 | `GET /api/v1/checkout/sessions/{sessionToken}` | statut checkout recupere et reponse normalisee | A faire |
| SBX-P1-003 | `POST /api/v1/payments/initiate` | payin direct initie et reponse normalisee | A faire |
| SBX-P1-004 | `GET /api/v1/payments/{token}/status` | statut payin recupere et reponse normalisee | A faire |
| SBX-P1-005 | `GET /api/v1/merchant/wallet/balance` | solde wallet recupere et reponse normalisee | A faire |
| SBX-P1-006 | `POST /api/v1/payouts/estimate` | estimation payout retournee et normalisee | A faire |
| SBX-P1-007 | `POST /api/v1/payouts` | payout test initie et reponse normalisee | A faire |
| SBX-P1-008 | `GET /api/v1/payouts/{id}` | statut payout recupere et reponse normalisee | A faire |
| SBX-P1-009 | Page admin `/admin/senepay-sandbox` | tests techniques accessibles aux admins uniquement | A faire |
| SBX-P1-010 | Journaux de test Sandbox | requete, reponse, statut SenePay, reference interne et erreur visibles | A faire |
| SBX-P1-011 | Tests unitaires mock HTTP | aucune requete reelle SenePay pendant les tests | A faire |

## Phase 2 - Validation reelle Sandbox

Cette phase ne vise plus a coder davantage, mais a prouver que le provider fonctionne reellement contre SenePay Sandbox.

| ID | Cas reel Sandbox | Objectif | Resultat attendu | Statut |
| --- | --- | --- | --- | --- |
| SBX-P2-001 | Wallet Balance | verifier authentification, headers et structure de reponse | solde recupere sans logique metier | Valide avec reserve TLS locale |
| SBX-P2-002 | Payout Estimate `100000 GNF` / Orange Guinee puis `100000 XOF` / Orange Senegal | verifier frais exacts, operateurs et codes pays | estimation valide et champs confirms | Valide |
| SBX-P2-003 | Checkout Session `5000 XOF` / Orange Senegal | recuperer `checkoutUrl` et lancer un paiement test | session creee et parcours testable | Partiellement valide |
| SBX-P2-004 | Webhook Sandbox | verifier signature, horodatage, idempotence et mise a jour d'etat | webhook exploitable comme en production | A faire |
| SBX-P2-005 | Payin/Payout test reel Sandbox | tester des montants de reference dans les deux sens | statuts et reponses reels verifies | A faire |

## Regle d'acceptation EPIC

L'EPIC `SenePay Sandbox - Phase 1` est considere :

- accepte sous reserve de validation Sandbox reelle.

L'integration SenePay ne sera consideree comme reellement validee qu'apres succes de la Phase 2 ci-dessus.

## Notes de validation reelle

### SBX-P2-001 - Wallet Balance

Date du test : `2026-07-08`

Constats :

- les cles `SENEPAY_PUBLIC_KEY` et `SENEPAY_SECRET_KEY` sont bien chargees localement ;
- la documentation locale SenePay confirme que cet endpoint accepte les cles API `X-Api-Key` et `X-Api-Secret`, ou un `JWT Bearer` ;
- le provider a ete corrige pour utiliser `X-Api-Key` et `X-Api-Secret` ;
- l'appel HTTPS standard echoue encore actuellement sur une verification de certificat TLS dans l'environnement local ;
- un appel de diagnostic sans verification SSL atteint bien l'endpoint ;
- avec les bons headers API, l'endpoint repond `200 OK` avec :
  - `{"message":"Solde recupere avec succes.","data":{"balance":0.0,"currency":"XOF","updatedAt":"2026-06-27T13:55:12.639038"}}`

Conclusion :

- la connectivite reseau vers `api.sene-pay.com` existe ;
- l'authentification provider via `X-Api-Key` et `X-Api-Secret` fonctionne ;
- la structure de reponse reelle est connue ;
- le blocage restant est local et porte sur la verification TLS standard.

Impact :

- avant de poursuivre idealement les autres tests reels via l'application elle-meme, il faut traiter ou contourner proprement la verification TLS locale ;
- sur le plan fonctionnel provider, `SBX-P2-001` est valide.

### SBX-P2-002 - Payout Estimate

Date du test : `2026-07-08`

Payload minimal confirme par la documentation et valide en pratique :

```json
{
  "amount": 100000,
  "country": "GN",
  "operator": "orange"
}
```

Constats :

- les premiers essais ont retourne `500 INTERNAL_ERROR` car le payload envoye ne suivait pas le schema reelement attendu par `POST /api/v1/payouts/estimate` ;
- la documentation locale confirme que l'endpoint attend un payload minimal :
  - `amount`
  - `country`
  - `operator`
- apres correction du mapping provider/service, les appels reels Sandbox ont reussi.

Resultats reels observes :

1. `100000 GNF` / `GN` / `orange`
   - `fees.provider = 2950`
   - `fees.total = 2950`
   - `net_amount = 97050`
   - `total_debit = 100000`

2. `100000 XOF` / `SN` / `orange`
   - `fees.provider = 1770`
   - `fees.total = 1770`
   - `net_amount = 98230`
   - `total_debit = 100000`

Conclusions :

- les codes pays `GN` et `SN` sont acceptes ;
- l'operateur `orange` est accepte en minuscules ;
- SenePay ne preleve pas de frais supplementaires sur cet endpoint (`fees.senepay = 0`) ;
- le cout provider est different selon le pays et la devise ;
- `total_debit` reste egal au montant, et les frais sont preleves sur le net recu.

Impact metier :

- ces donnees sont exploitables pour alimenter les futures formules de pricing ;
- elles donnent une premiere base de comparaison reelle entre cout fournisseur SenePay et couts terrain.

### SBX-P2-003 - Checkout Session

Date du test : `2026-07-08`

Payload teste :

```json
{
  "amount": 5000,
  "currency": "XOF",
  "orderReference": "ACX-SBX-CHK-001",
  "description": "Test checkout Sandbox AfricaChangeX",
  "returnUrl": "https://example.com/success",
  "cancelUrl": "https://example.com/cancel",
  "webhookUrl": "https://example.com/webhooks/senepay",
  "country": "SN"
}
```

Resultats reels observes :

- creation de session : `200 OK`
- `sessionToken` retourne : `GNEWdO72haJsJzKIxtZNu9HjeTcfibFR`
- `checkoutUrl` retourne :
  - `https://api.sene-pay.com/checkoutSandBox.html?session=GNEWdO72haJsJzKIxtZNu9HjeTcfibFR`
- `status` initial : `Open`

Verification de statut :

- appel `GET /api/v1/checkout/sessions/{sessionToken}` reussi ;
- statut confirme : `Open`
- `payment = null`

Conclusion :

- la creation de checkout session fonctionne ;
- l'URL Sandbox retournee est correcte ;
- le polling de statut de session fonctionne ;
- le paiement test lui-meme n'a pas encore ete execute dans l'interface checkout ;
- le webhook reste donc a valider a l'etape suivante.
