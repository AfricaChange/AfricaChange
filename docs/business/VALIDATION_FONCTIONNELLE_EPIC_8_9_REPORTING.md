# Validation Fonctionnelle EPIC 8.9 - Reporting Engine

## Objectif

Verifier que les chiffres du dashboard admin read-only correspondent exactement :

- aux donnees sources `Conversion` et `ConversionExecution` ;
- aux calculs du `ProfitabilityEngine` ;
- aux agregats filtres par corridor, devise, marchand, mode et statut.

## Jeu de donnees controle

| Reference | Cas | Mode | Statut | Provisoire | Marge estimee | Marge reelle attendue | Ecart attendu |
| --- | --- | --- | --- | --- | ---: | ---: | ---: |
| `CNV-VAL-001` | Conversion rentable | `platform` | `completed` | non | 5 000 | 4 000 | -1 000 |
| `CNV-VAL-002` | Conversion en perte | `merchant` | `completed` | non | 10 000 | -20 000 | -30 000 |
| `CNV-VAL-003` | Conversion provisoire | `hybrid` | `payout_processing` | oui | 12 000 | 9 000 | -3 000 |
| `CNV-VAL-004` | Conversion mode platform | `platform` | `completed` | non | 15 000 | 10 000 | -5 000 |
| `CNV-VAL-005` | Conversion mode merchant | `merchant` | `completed` | non | 3 000 | 2 500 | -500 |
| `CNV-VAL-006` | Conversion mode hybrid | `hybrid` | `completed` | non | 25 | 15 | -10 |
| `CNV-VAL-007` | Conversion annulee | `platform` | `cancelled` | non | 4 000 | 4 000 | 0 |
| `CNV-VAL-008` | Conversion rejetee | `platform` | `rejected` | non | 5 000 | 5 000 | 0 |

## Resultats observes

Les tests d'integration verifient :

- les volumes comptabilises ;
- la marge estimee ;
- la marge reelle ;
- l'ecart prevision / reel ;
- le corridor ;
- la devise cible ;
- le segment client ;
- le mode d'execution ;
- la distinction provisoire / definitif ;
- l'absence de double comptage ;
- la coherence des filtres ;
- l'absence totale d'ecriture ou de mutation de donnees.

## Ecarts identifies

Aucun ecart fonctionnel non explique n'a ete observe sur le jeu de donnees controle.

## Tests de reference

- `tests/test_reporting_validation_integration.py`
- `tests/test_reporting_service.py`
- `tests/test_reporting_engine.py`
- `tests/test_admin_reporting_route.py`
