# Matrice de Tracabilite

## EPIC 8.9 - Reporting Engine

| Regle metier | Document | Service cible | Tests cibles |
| --- | --- | --- | --- |
| Reporting par corridor | `docs/business/VALIDATION_FONCTIONNELLE_EPIC_8_9_REPORTING.md` | `engines/reporting_engine/reporting_engine.py` | `tests/test_reporting_engine.py` |
| Reporting par devise | `docs/business/VALIDATION_FONCTIONNELLE_EPIC_8_9_REPORTING.md` | `engines/reporting_engine/reporting_engine.py` | `tests/test_reporting_engine.py` |
| Reporting par mode d'execution | `docs/business/VALIDATION_FONCTIONNELLE_EPIC_8_9_REPORTING.md` | `engines/reporting_engine/reporting_engine.py` | `tests/test_reporting_engine.py` |
| Reporting par marchand | `docs/business/VALIDATION_FONCTIONNELLE_EPIC_8_9_REPORTING.md` | `engines/reporting_engine/reporting_engine.py` / `services/reporting_service.py` | `tests/test_reporting_engine.py` / `tests/test_reporting_service.py` |
| Reporting par segment client | `docs/business/VALIDATION_FONCTIONNELLE_EPIC_8_9_REPORTING.md` | `engines/reporting_engine/reporting_engine.py` | `tests/test_reporting_engine.py` |
| Transactions en perte | `docs/business/VALIDATION_FONCTIONNELLE_EPIC_8_9_REPORTING.md` | `services/reporting_service.py` | `tests/test_reporting_service.py` / `tests/test_reporting_validation_integration.py` |
| Ecart prevision / reel | `docs/business/VALIDATION_FONCTIONNELLE_EPIC_8_9_REPORTING.md` | `services/reporting_service.py` | `tests/test_reporting_validation_integration.py` |
| Separation provisoire / definitif | `docs/business/VALIDATION_FONCTIONNELLE_EPIC_8_9_REPORTING.md` | `services/reporting_service.py` | `tests/test_reporting_service.py` / `tests/test_reporting_validation_integration.py` |
| Dashboard admin read-only | `docs/business/VALIDATION_FONCTIONNELLE_EPIC_8_9_REPORTING.md` | `routes/admin.py` / `services/reporting_service.py` | `tests/test_admin_reporting_route.py` |
