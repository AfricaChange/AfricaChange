# Changelog

## 2026-06-28
- creation des documents de gouvernance manquants a la racine
- introduction du squelette modulaire `providers/`
- introduction du squelette modulaire `engines/`
- introduction du squelette modulaire `webhooks/`
- ajout d'un registre provider et d'une factory provider de base
- ajout d'un provider `SenePay` de reference

## 2026-06-28 - Gouvernance architecture renforcee
- ajout de la gouvernance par EPIC dans `PROJECT_MASTER.md`
- formalisation des ADR sur `Decimal`, wallets, provider adapter et revue obligatoire
- ajout de `docs/architecture/ARCHITECT_REVIEW.md`

## 2026-06-28 - Passage en Phase 2
- formalisation de `Phase 2 - Infrastructure Fintech`
- ajout de la vision produit panafricaine
- ajout du cadre `Core / Business / Interfaces`
- ajout de l'EPIC 9 `Core financier`
- ajout de l'approche par domaines metier

## 2026-06-28 - EPIC 8 multi-currency wallet
- ajout de `Currency`, `MerchantBalance` et `WalletEntry`
- ajout du `WalletTransactionManager` et du `WalletService`
- branchement de la liquidite marchand et des settlements sur le wallet multi-devises
- ajout d'une migration wallet multi-devises
- ajout des tests wallet, liquidite et dashboard

## 2026-06-28 - EPIC 8.5 wallet administration
- ajout de `merchant_wallet_admin_service.py` pour les operations admin wallet
- ajout de la route admin `marchands/<id>/wallet` et de la page `admin_merchant_wallet.html`
- ajout de `AdminWalletAction` pour tracer les actions admin wallet
- ajout des controles: motif obligatoire, devise active, reference garantie, confirmation sur montant sensible
- ajout de l'historique admin wallet dans l'interface
- ajout des tests unitaires et d'integration admin wallet
