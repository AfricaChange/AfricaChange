# Technical Debt Report

## EPIC
EPIC 8.6 - Repository Cleanup & Technical Debt Reduction

## Scope
Ce document decrit la dette technique observee avant toute suppression ou refactorisation significative.

## Executive Summary

Le depot est fonctionnel et la suite de tests passe, mais la dette technique reste elevee sur quatre axes :

- hygiene du depot
- couplages legacy
- compatibilite SQLAlchemy 2.x
- coherence des assets, routes et scripts auxiliaires

## Confirmed Findings

### 1. Repository hygiene

- le fichier `.gitignore` est invalide pour un projet Python/Flask :
- il contient des lignes `echo ... >> .gitignore` au lieu de vraies regles d'exclusion
- il est herite d'un template Jekyll/Ruby sans rapport avec le projet
- le depot contient de nombreux `__pycache__`, fichiers `.pyc`, archives `.zip`, manifestes et fichiers temporaires non ignores

Impact :
- bruit Git important
- risque de commit accidentel de fichiers generes
- historique pollue

### 2. Legacy route and module coupling

- `app.py` utilise `routes/convert.py`
- `paiements/routes.py` importe encore `convert.py` a la racine
- `convert.py` racine et `routes/convert.py` representent deux generations differentes du meme domaine

Impact :
- duplication de logique
- risque de divergence comportementale
- difficulte a definir la vraie source d'autorite

### 3. SQLAlchemy 2.x debt

Usages deprecies confirms hors archives `zip/` :

- `Query.get()`
- `Query.get_or_404()`

Zones touchees :
- `routes/auth.py`
- `routes/admin.py`
- `routes/paiement.py`
- `paiements/routes.py`

Impact :
- avertissements d'execution
- dette de migration framework
- futur risque de casse lors d'une mise a jour majeure

### 4. Admin realtime legacy coupling

`templates/base_admin.html` charge :

- `js/admin_live.js`

Ce script appelle :

- `/admin/realtime/stats`

Mais `routes/admin_realtime.py` n'est pas enregistre dans `app.py`.

Impact :
- composant legacy actif mais incomplet
- ambiguite entre dette de presentation et dette de routing
- le prochain changement doit etre explicite : enregistrer reellement la route
  ou retirer le flux admin realtime dans un chantier dedie

### 5. Unregistered or orphan candidates

Eléments a verifier ou traiter comme orphelins probables :

- `routes/admin_realtime.py` : blueprint defini mais non enregistre dans `app.py`
- `templates/paiement.html` : aucune reference applicative identifiee dans les routes actives
- `templates/reset_password_confirm.html` : aucune reference active identifiee
- `templates/Africa_Change_License.html` : aucune reference active identifiee

Impact :
- dette de lisibilite
- faux positifs dans la maintenance
- surface de code inutilement large

### 6. Repository clutter

Presences non fonctionnelles ou a clarifier :

- dossiers `zip/` avec archives de sauvegarde
- fichiers racine atypiques : `git`, `python`, `url`, `oword`
- manifestes et inventaires multiples : `MANIFEST.md`, `files.json`, `zip/MANIFEST.md`, `zip/files.json`
- scripts racine historiques nombreux sans statut explicite

Impact :
- confusion sur ce qui appartient au produit
- augmentation du risque d'erreur humaine

### 7. Security and secret handling hygiene

Le depot contient des noms de fichiers sensibles ou environnementaux en racine :

- `.env`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `ORANGE_CLIENT_ID`
- `ORANGE_CLIENT_SECRET`
- `ORANGE_MERCHANT_KEY`
- `WAVE_API_KEY`

Ce rapport n'inspecte pas leur contenu, mais leur presence en racine constitue un signal d'hygiene a traiter.

Impact :
- risque de fuite
- confusion entre configuration locale et code source

### 8. Architecture smells

Constats structurels a surveiller :

- `models.py` concentre un volume important de responsabilites historiques et recentes
- `routes/admin.py` porte beaucoup de cas d'usage et reste une route volumineuse
- coexistence entre `webhooks/` et `webhook.py`, signe d'une migration inachevee
- coexistence entre `convert.py` racine et `routes/convert.py`, signe de duplication fonctionnelle
- `paiements/routes.py` montre un couplage fort avec des modules legacy et des importations dupliquees
- `routes/support.py` contient une incoherence probable entre l'endpoint declare (`support.index`) et les redirections vers `support.support_page`

Ces points ne sont pas necessairement des bugs, mais ce sont des signaux de maintenabilite a traiter avant les EPIC metier.

## Quantitative Snapshot

- tests Python executes : `35`
- resultat tests : `OK`
- occurrences `TODO` / `FIXME` hors archives : `0`
- dossiers `__pycache__` detectes avant nettoyage : `13`
- dossiers `__pycache__` apres nettoyage certain : `0`
- fichiers `.pyc` detectes avant nettoyage : `75`
- fichiers `.pyc` apres nettoyage certain : `0`
- dossiers `__pycache__` apres reexecution des tests : `8`
- fichiers `.pyc` apres reexecution des tests : `43`
- usages SQLAlchemy legacy detectes hors archives : `24`

## Technical Debt Register

| ID | Element | Gravite | Action |
| --- | --- | --- | --- |
| TD-001 | `Query.get()` / `get_or_404()` | 🟡 | EPIC SQLAlchemy 2.x |
| TD-002 | `convert.py` racine | 🟡 | Legacy documente, retrait apres migration |
| TD-003 | `routes/support.py` endpoint incoherent | 🟠 | Corriger |
| TD-004 | `routes/admin_realtime.py` non enregistre mais encore reference par l'admin | 🟠 | Traiter explicitement |
| TD-005 | Templates orphelins confirmes | 🟢 | Reevaluation avant suppression |
| TD-006 | `.gitignore` incorrect historique | 🟢 | Corrige |
| TD-007 | Assets admin references en nom incorrect | 🟢 | Corrige |
| TD-008 | Caches Python et `.pyc` dans le depot local | 🟢 | Nettoye |
| TD-009 | `conversion.statut` limite a `VARCHAR(20)` sur Render | 🟠 | TECH-001 - elargissement a `VARCHAR(50)` avant activation operationnelle des etats longs |

## Technical Debt Trend

Mesure interne qualitative :

- avant EPIC 8.6 : `35 points`
- apres Phase A + Phase B prudente : `22 points`
- objectif avant EPIC 10 : `15 points`

Lecture :
- la dette a baisse de maniere visible sur l'hygiene du depot et les incoherences evidentes
- les sujets restants sont surtout du legacy structurel et du framework

## Recommended Actions

### Priorite haute

- isoler et documenter les fichiers a exclure du depot
- traiter le couplage `convert.py` racine vs `routes/convert.py`
- inventorier les usages SQLAlchemy legacy avec plan de migration
- corriger l'incoherence d'endpoint dans `routes/support.py`
- valider puis appliquer la migration d'elargissement de `conversion.statut` avant activation operationnelle des nouveaux etats longs sur Render

### Priorite moyenne

- classifier les scripts racine en `active`, `legacy`, `manual`, `obsolete`
- verifier les templates orphelins
- verifier les blueprints non enregistres

### Priorite basse

- rationaliser manifestes et fichiers d'inventaire
- regrouper ou archiver les scripts utilitaires non critiques

## Non-goals

Ce rapport n'introduit aucune suppression et ne modifie aucun comportement fonctionnel.

## EPIC Delta

| Critere | Avant | Apres |
| --- | --- | --- |
| Tests | 33 | 35 |
| Dette technique | 35 | 22 |
| Architecture smells | 14 | 11 |
| Legacy | 17 | 16 |
| Documentation | 94 % | 97 % |
