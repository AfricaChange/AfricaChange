# Diagnostic TLS - SenePay Sandbox

## Objectif

Ce document conserve la trace du probleme TLS local rencontre pendant la validation reelle Sandbox du provider SenePay.

Son but est d'eviter de rediagnostiquer le meme probleme plus tard sur :

- une autre machine locale,
- un environnement CI/CD,
- un serveur de preproduction,
- une future machine de production.

## Contexte

Lors du test reel `SBX-P2-001 - Wallet Balance`, AfricaChangeX a pu :

- charger les cles Sandbox,
- joindre `https://api.sene-pay.com`,
- corriger l'authentification provider vers `X-Api-Key` et `X-Api-Secret`,
- obtenir une reponse `200 OK` via un test de diagnostic reseau.

Cependant, l'appel HTTPS standard via Python a echoue localement sur la verification du certificat TLS.

## Erreur exacte observee

Erreur retournee par Python `requests` :

`SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1131)')`

## Environnement technique observe

- OS : Windows
- Python : `3.8.10`
- OpenSSL : `OpenSSL 1.1.1k 25 Mar 2021`
- certifi : `2025.10.05`

## Difficultes identifiees

### 1. Inspection HTTPS locale Avast

Le certificat effectivement presente a Python pour `api.sene-pay.com` etait emis par :

- `Avast Web/Mail Shield Root`

Cela signifie qu'un composant local Avast intercepte le trafic HTTPS et presente un certificat racine localement approuve par Windows, mais pas connu du bundle `certifi` de Python.

### 2. Variables proxy parasites

Les variables d'environnement suivantes etaient positionnees localement :

- `HTTP_PROXY=http://127.0.0.1:9`
- `HTTPS_PROXY=http://127.0.0.1:9`
- `ALL_PROXY=http://127.0.0.1:9`
- `GIT_HTTP_PROXY=http://127.0.0.1:9`
- `GIT_HTTPS_PROXY=http://127.0.0.1:9`

Ces variables poussaient Python `requests` a essayer de sortir via un faux proxy local.

## Decision d'architecture

AfricaChangeX choisit officiellement :

- de corriger proprement le probleme TLS local,
- et de ne pas utiliser `verify=False` dans le provider comme solution normale.

### Regle stricte

`verify=False` est refuse :

- en production,
- dans le provider standard,
- comme solution definitive.

Une exception temporaire ne serait acceptable que dans un mode de debug local strictement encadre, jamais active par defaut et jamais utilise en production.

## Cause fonctionnelle eliminee

Le probleme n'est plus l'authentification.

La documentation locale `senepay-api-docs.md` confirme que les endpoints publics serveur utilisent :

- `X-Api-Key`
- `X-Api-Secret`

Apres correction du provider, la reponse reelle `200 OK` du endpoint `wallet balance` a confirme que :

- les cles sont valides,
- le mapping d'authentification est correct,
- l'API SenePay Sandbox repond.

## Causes probables

Sous Windows, les causes probables incluent :

1. bundle CA Python / certifi obsolete ;
2. inspection HTTPS locale par antivirus, proxy ou pare-feu ;
3. certificat intermediaire manquant ou mal resolu par l'environnement Python ;
4. difference entre le magasin de certificats du navigateur et celui utilise par Python.

## Diagnostic reel observe

1. appel `wallet balance` avec `Authorization: Bearer ...`
   - reponse : `401 UNAUTHORIZED`
2. lecture de la documentation locale SenePay
   - confirmation que l'authentification attendue est `X-Api-Key` + `X-Api-Secret`
3. correction du provider
   - l'appel de diagnostic sans verification SSL retourne `200 OK`
4. verification TLS standard
   - echoue a cause du certificat racine Avast non present dans `certifi`
5. neutralisation des variables proxy parasites
   - supprime un second blocage machine
6. construction d'un bundle local `certifi + Avast Root` en format PEM
   - l'appel HTTPS standard via `requests` fonctionne ensuite correctement

## Etat du provider

Le provider SenePay est maintenant considere comme :

- `CONNECTE`

Mais pas encore :

- `VALIDE`

## Conditions pour passer a VALIDE

| ID | Test | Etat |
| --- | --- | --- |
| SBX-P2-001 | Wallet Balance | Valide |
| SBX-P2-002 | Payout Estimate | En attente |
| SBX-P2-003 | Checkout Session | En attente |
| SBX-P2-004 | Webhook | En attente |
| SBX-P2-005 | Payin/Payout Sandbox | En attente |

## Solution retenue

La solution retenue est :

- corriger la chaine TLS locale proprement,
- neutraliser les variables proxy parasites,
- puis poursuivre les tests reels Sandbox avec verification HTTPS normale.

## Correctif local reproductible

Fichiers crees localement dans le workspace :

- `certs/avast-root.cer`
- `certs/avast-root.pem`
- `certs/python-tls-bundle.pem`

Principe :

- exporter le certificat racine Avast depuis le magasin Windows ;
- le convertir en PEM ;
- le concatener au bundle `certifi` de Python ;
- exposer ce bundle via `REQUESTS_CA_BUNDLE`.

Variables a neutraliser avant test :

- `HTTP_PROXY`
- `HTTPS_PROXY`
- `ALL_PROXY`
- `GIT_HTTP_PROXY`
- `GIT_HTTPS_PROXY`

Variables utiles pour le test :

- `REQUESTS_CA_BUNDLE=...\\certs\\python-tls-bundle.pem`
- ou `AFRICACHANGEX_CUSTOM_CA_BUNDLE=...\\certs\\python-tls-bundle.pem`

## Decision d'implementation

Le provider SenePay peut lire optionnellement :

- `AFRICACHANGEX_CUSTOM_CA_BUNDLE`

Cette option est reservee a l'environnement d'execution et ne doit pas devenir un contournement code en dur dans le provider.

## Etapes recommandees

1. verifier la version de `certifi` ;
2. verifier la version OpenSSL utilisee par Python ;
3. verifier si un proxy ou antivirus injecte un certificat local ;
4. verifier les variables proxy locales ;
5. retester `wallet balance` en HTTPS standard ;
5. poursuivre ensuite les tests `SBX-P2-002` a `SBX-P2-005`.

## Rappel de gouvernance

Le provider ne doit pas integrer de contournement TLS non maitrise.

Le but de cette phase Sandbox est de valider une integration propre, reproductible et industrialisable.
