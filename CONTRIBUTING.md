# Contributing

## Regles generales
- Lire `PROJECT_MASTER.md` avant tout chantier structurant.
- Respecter `ARCHITECTURE_DECISIONS.md`.
- Garder les routes legeres.
- Garder la logique metier dans les services ou engines.
- Ajouter des tests pour toute nouvelle logique metier.
- Aucun module structurant ne commence sans specification validee.

## Structure cible
- `core/` pour le coeur financier
- `providers/` pour les integrations fournisseurs
- `engines/` pour les moteurs metier
- `webhooks/` pour la reception et l'orchestration des callbacks
- `services/` pour l'orchestration applicative
- `docs/architecture/` pour les revues et validations d'EPIC

## Couches cibles
- Core : manipule l'argent
- Business : orchestre les cas d'usage
- Interfaces : Flask, admin, mobile, API publique

## Regles pour les providers
- heriter de `providers.base_provider.BaseProvider`
- implementer l'interface commune
- retourner des structures normalisees
- ne pas exposer la logique fournisseur aux routes
- ne jamais contenir de logique metier AfricaChangeX

## Regles pour les engines
- pas d'acces direct depuis les templates
- API claire, testable, documentee
- aucune hypothese hardcodee sur un pays ou un fournisseur si cela peut etre abstrait
- les moteurs financiers critiques doivent etre independants des providers

## Regles pour les donnees financieres
- toute nouvelle table financiere doit utiliser `Decimal` / `NUMERIC`
- toute mutation financiere doit etre transactionnelle
- toute ecriture doit etre reliee a un contexte metier exploitable en audit
- aucune interface ou route ne doit modifier directement un solde

## Cycle de travail obligatoire
- idee
- specification
- revue d'architecture
- validation
- implementation
- tests
- documentation
- fusion

## Regles Git
- ne jamais pousser directement sur `main`
- utiliser une branche metier explicite de type `feature/`, `release/` ou `hotfix/`
- privilegier des commits decoupes par domaine fonctionnel ou EPIC
- adopter les Conventional Commits : `feat(...)`, `fix(...)`, `refactor(...)`, `docs(...)`, `test(...)`, `chore(...)`
- ouvrir une Pull Request pour toute evolution structurante, meme en travail solo

## Regles de commit
- aucun commit fonctionnel sans tests executes
- chaque commit ou PR doit mentionner les validations executees
- exemples de validations minimales :
- `python -m unittest discover -s tests`
- `python -m py_compile`
- `alembic upgrade head`
- import applicatif principal

## Documentation
- mettre a jour `CHANGELOG.md`
- mettre a jour `ROADMAP.md`
- mettre a jour `ARCHITECTURE_DECISIONS.md` si une decision change
- mettre a jour `docs/architecture/ARCHITECT_REVIEW.md` pour chaque EPIC structurant

## Tests minimaux
- test unitaire de chaque nouveau module critique
- verification d'import de l'application si le module est branche
