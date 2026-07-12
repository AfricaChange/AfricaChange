# Changelog

## 2026-07-12 - EPIC 8.9 Reporting Engine v1.0

- ajout du module `engines/profitability_engine/` comme dependance minimale de calcul de rentabilite pour le reporting
- ajout du module `engines/reporting_engine/` pour les agregats par corridor, devise, mode, marchand et segment client
- ajout de `ConversionExecution` et des champs de lecture necessaires sur `Conversion`
- ajout de la migration `reporting_foundation` pour rendre ces lectures deployables sur une base `main` existante
- ajout du service `services/reporting_service.py`
- ajout de la route admin read-only `/admin/reporting`
- ajout du dashboard `templates/admin_reporting.html`
- ajout des tests de reporting, de route admin et de validation fonctionnelle controlee
- EPIC 8.9 marque comme valide et ferme
