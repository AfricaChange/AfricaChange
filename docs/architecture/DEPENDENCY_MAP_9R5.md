# EPIC 9.R5 - Dependency Map

## Objective
This note captures the structural reading used during EPIC 9.R5.

## Layer reading

### Presentation
- `app.py`
- `routes/`
- `webhook.py`
- `templates/`
- `static/`

### Application
- `services/` orchestrators, repositories and workflow services
- `paiements/routes.py` as a historical payment application entrypoint

### Domain
- `engines/`
- contract-oriented merchant state, workflow and lifecycle modules in `services/`

### Infrastructure
- `database.py`
- `providers/`
- `services/providers/`
- SQLAlchemy repositories inside `services/`

### Shared / Cross-cutting
- `config.py`
- `extensions.py`
- `services/constants.py`
- `app_bootstrap/`

## Key structural findings

1. `app.py` had accumulated bootstrap, request hooks, security headers,
   observability, blueprint registration and error handlers in one place.
2. `models.py` remains the historical SQLAlchemy authority and should not be
   split mechanically without a dedicated aggregate migration plan.
3. Two provider families coexist:
   - `providers/` for the canonical provider registry
   - `services/providers/` for legacy payment-route integrations
4. `routes/admin_realtime.py` is still active legacy:
   - not registered in Flask
   - still referenced by `static/js/admin_live.js`
   - still indirectly loaded by `templates/base_admin.html`

## R5 decisions

- Extract technical Flask bootstrap responsibilities into `app_bootstrap/`.
- Keep `models.py` monolithic for now and only clarify its role.
- Keep `routes/admin_realtime.py` unregistered until a dedicated behavioural
  decision is taken.
- Document the provider split instead of forcing a risky contract merge.
