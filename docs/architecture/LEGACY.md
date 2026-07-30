# Legacy Inventory

## Purpose
Ce document liste les elements legacy a conserver temporairement, les candidats a retrait et les zones de transition a surveiller.

## Legacy kept temporarily

### Merchant legacy balances

Elements :

- `Merchant.solde_disponible`
- `Merchant.solde_verrouille`

Statut :
- legacy conserve temporairement

Pourquoi ils existent encore :
- retrocompatibilite pendant la transition vers `MerchantBalance`
- certaines vues et certains flux historiques les lisent encore indirectement

Element cible :
- `MerchantBalance` par devise via `WalletService`

### Root `convert.py`

Statut :
- legacy actif indirect

Pourquoi il ne doit pas etre supprime immediatement :
- `paiements/routes.py` l'importe encore

Element cible :
- `routes/convert.py` et services de conversion modularises

### Historical operational scripts at repository root

Exemples :

- `create_admin.py`
- `create_tables.py`
- `sync_db.py`
- `reset_pg.py`
- `migrate_sqlite_to_postgres.py`
- `insert_comptes.py`
- `mode_manuel.py`
- `test-manuel.py`

Statut :
- legacy operationnel non classe

Pourquoi ils ne doivent pas etre supprimes sans audit :
- usage manuel possible hors flux applicatif
- certains peuvent encore servir de support d'exploitation

Action attendue :
- classifier chaque script : `actif`, `legacy`, `obsolete`

### Classification initiale des scripts racine

#### Scripts actifs / utiles

- `admin_manager.py` : utilitaire manuel de gestion admin
- `check_env.py` : audit environnement / securite locale
- `check_postgres.py` : verification de connexion et tables PostgreSQL
- `insert_comptes.py` : initialisation manuelle de comptes systeme
- `migrate_sqlite_to_postgres.py` : migration ponctuelle documentee
- `package_project.py` : packaging projet
- `package_release.py` : packaging release
- `reset_pg.py` : reset manuel PostgreSQL

#### Scripts legacy retires apres audit

- `mode_manuel.py` : comportement remplace fonctionnellement par le Payment Mode global, sans reference runtime active
- `test-manuel.py` : script manuel lie a l'ancien `mode_systeme`, sans reference runtime active

#### Scripts historiques obsoletes

- `create_admin.py`
- `create_tables.py`
- `sync_db.py`

Statut :
- suppressions autorisees apres verification de l'absence de references runtime

## Legacy candidates to retire

### Broken admin asset naming

Elements :

- references template en kebab-case
- fichiers reels en snake_case

Statut :
- dette de presentation / front admin

Remplacement attendu :
- conventions de nommage uniformes et assets resolus

### Unregistered blueprint

Element :
- `routes/admin_realtime.py`

Statut :
- a conserver provisoirement

Pourquoi il n'est pas supprime dans l'immediat :
- `static/js/admin_live.js` appelle encore `/admin/realtime/stats`
- `templates/base_admin.html` charge encore `js/admin_live.js`
- il s'agit donc d'un composant casse / incomplet, pas d'un code mort demontre

Remplacement attendu :
- enregistrement reel ou suppression documentee

### Orphan template candidates

Elements confirmes orphelins :

- `templates/paiement.html`
- `templates/reset_password_confirm.html`
- `templates/Africa_Change_License.html`

Justification :
- aucune reference applicative active identifiee hors manifestes, inventaires ou archives

Elements probablement orphelins :

- aucun autre template classe a ce stade

Elements a verifier plus tard :

- templates rendus dynamiquement sans `render_template` direct

Statut :
- retires apres verification de l'absence de references applicatives actives

Regle :
- ne rien supprimer avant verification definitive des references runtime

## Legacy framework debt

### SQLAlchemy legacy query API

Elements :

- `Query.get()`
- `Query.get_or_404()`

Statut :
- legacy framework

Plan cible :
- migration progressive vers l'API SQLAlchemy 2.x / `Session.get()`

## Legacy repository content

Elements :

- dossiers `zip/` de sauvegarde
- `__pycache__/`
- `*.pyc`
- manifestes multiples
- fichiers racine atypiques : `git`, `python`, `url`, `oword`

Statut :
- clutter / hygiene debt

Regle :
- suppression seulement apres demonstration d'inutilite

## Legacy handling rules

- tout element legacy conserve doit etre nomme explicitement dans les rapports
- tout retrait doit expliquer :
- pourquoi
- quel element le remplace
- aucun element legacy critique ne doit etre retire sans tests verts
