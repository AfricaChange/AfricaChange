# Contrat Provider - SenePay

## Objectif

Ce document définit le contrat technique public du provider `SenePay`.

Il sert de référence pour :

- l'intégration Sandbox,
- l'intégration future en production,
- l'harmonisation multi-fournisseurs,
- la traçabilité entre provider, services et tests.

## Règle

Tout provider futur devra tendre vers le même contrat de sortie normalisée, même si le fournisseur réel expose :

- des champs différents,
- des statuts différents,
- des erreurs différentes,
- des formats différents.

Le rôle du provider est d'adapter.

Le rôle du métier n'est pas de connaître les détails bruts du fournisseur.

## Sortie Normalisée Minimale

Toutes les méthodes publiques du provider doivent retourner une structure compatible avec :

```json
{
  "success": true,
  "provider": "senepay",
  "operation": "nom_operation",
  "reference": "reference_provider_ou_reference_technique",
  "status": "pending|success|failed|unknown|configuration_error|request_error",
  "message": "message lisible",
  "payload": {
    "request": {},
    "response": {},
    "http_status_code": 200
  }
}
```

## Méthodes Publiques

### 1. `payin(**kwargs)`

#### Rôle

Wrapper générique du contrat provider commun.

Pour `SenePay`, cette méthode délègue au payin direct technique.

#### Entrées possibles

- `reference`
- `amount`
- `currency`
- `phone_number`
- `operator`

#### Sortie normalisée

- `operation = "payin"`
- `reference`
- `status`
- `payload.request`
- `payload.response`

#### Erreurs possibles

- `configuration_error`
- `request_error`
- erreur HTTP fournisseur

### 2. `payout(**kwargs)`

#### Rôle

Wrapper générique du contrat provider commun.

Pour `SenePay`, cette méthode délègue au payout technique.

#### Entrées possibles

- `reference`
- `amount`
- `currency`
- `beneficiary_name`
- `beneficiary_phone`
- `beneficiary_country`
- `beneficiary_currency`

#### Sortie normalisée

- `operation = "payout"`
- `reference`
- `status`
- `payload.request`
- `payload.response`

### 3. `get_status(reference, resource_type="payment")`

#### Rôle

Wrapper générique du contrat provider commun pour la récupération de statut.

#### Entrées

- `reference`
- `resource_type`
  - `payment`
  - `checkout`
  - `payout`

#### Sortie normalisée

- `operation = "status"`
- `status`
- `reference`

### 4. `get_balance(**kwargs)`

#### Rôle

Wrapper générique du contrat provider commun pour la consultation de solde.

#### Sortie normalisée

- `operation = "balance"`
- `status`
- `payload.response`

## Méthodes Techniques SenePay

### 5. `create_checkout_session(**kwargs)`

#### Endpoint cible

`POST /api/v1/checkout/sessions`

#### Entrées possibles

- `reference`
- `amount`
- `currency`
- `description`
- `return_url`
- `cancel_url`
- `customer_name`
- `customer_email`
- `customer_phone`

#### Sortie attendue

- `operation = "checkout_session_create"`
- `reference` : `sessionToken` si disponible
- `status`
- `payload.response`

### 6. `get_checkout_session_status(session_token)`

#### Endpoint cible

`GET /api/v1/checkout/sessions/{sessionToken}`

#### Entrée

- `session_token`

#### Sortie attendue

- `operation = "checkout_session_status"`
- `reference = session_token` ou référence provider renvoyée
- `status`

### 7. `initiate_direct_payin(**kwargs)`

#### Endpoint cible

`POST /api/v1/payments/initiate`

#### Entrées possibles

- `reference`
- `amount`
- `currency`
- `phone_number`
- `operator`

#### Sortie attendue

- `operation = "payin_direct_create"`
- `reference` : token ou référence retournée
- `status`

### 8. `get_direct_payin_status(token)`

#### Endpoint cible

`GET /api/v1/payments/{token}/status`

#### Entrée

- `token`

#### Sortie attendue

- `operation = "payin_direct_status"`
- `reference = token` ou référence provider
- `status`

### 9. `get_wallet_balance()`

#### Endpoint cible

`GET /api/v1/merchant/wallet/balance`

#### Sortie attendue

- `operation = "wallet_balance"`
- `status`
- `payload.response`

### 10. `estimate_payout(**kwargs)`

#### Endpoint cible

`POST /api/v1/payouts/estimate`

#### Entrées possibles

- `reference`
- `amount`
- `currency`
- `beneficiary_name`
- `beneficiary_phone`
- `beneficiary_country`
- `beneficiary_currency`

#### Sortie attendue

- `operation = "payout_estimate"`
- `status`
- `payload.response`

### 11. `create_payout(**kwargs)`

#### Endpoint cible

`POST /api/v1/payouts`

#### Entrées possibles

- `reference`
- `amount`
- `currency`
- `beneficiary_name`
- `beneficiary_phone`
- `beneficiary_country`
- `beneficiary_currency`

#### Sortie attendue

- `operation = "payout_create"`
- `reference`
- `status`

### 12. `get_payout_status(payout_id)`

#### Endpoint cible

`GET /api/v1/payouts/{id}`

#### Entrée

- `payout_id`

#### Sortie attendue

- `operation = "payout_status"`
- `reference = payout_id` ou référence provider
- `status`

## Webhooks

### 13. `verify_webhook(payload, headers)`

#### Rôle

Valider la signature du webhook si le secret est disponible.

#### Sortie

- `True` si la signature est valide
- `False` sinon

### 14. `handle_webhook(payload, headers)`

#### Rôle

Normaliser le traitement d'un webhook reçu.

#### Sortie attendue

- `operation = "webhook"`
- `success`
- `reference`
- `status`
- `message`

## Erreurs Techniques à Gérer

Le provider doit pouvoir normaliser au minimum :

- secret manquant
- erreur d'authentification
- timeout
- erreur réseau
- réponse non JSON
- statut HTTP en erreur
- statut provider inconnu

## Règle d'Évolution

Si demain :

- `OrangeProvider`
- `WaveProvider`
- `PayDunyaProvider`
- `CinetPayProvider`

sont intégrés, ils devront respecter la même philosophie :

- méthodes publiques stables,
- structure de sortie normalisée,
- détails fournisseur encapsulés dans le provider.

## Statut actuel du provider

Etat actuel :

- `CONNECTE`

Justification :

- l'authentification `X-Api-Key` / `X-Api-Secret` est validee sur un appel reel `wallet balance`,
- la communication avec l'API SenePay Sandbox fonctionne.

Le provider ne sera considere comme :

- `VALIDE`

qu'apres succes de l'ensemble de la Phase 2 Sandbox documentee dans :

- [SENEPAY_SANDBOX_TEST_MATRIX.md](/C:/Users/7MAKSACOD%20PC/Documents/Africa_change_project/africa-change-dev/docs/business/SENEPAY_SANDBOX_TEST_MATRIX.md)
