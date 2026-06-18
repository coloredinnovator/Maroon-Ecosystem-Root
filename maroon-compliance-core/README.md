# Maroon Compliance Core

> **Codex Reference:** §3.3 — Zero-Trust Gatekeeper

Every transaction across the Maroon Ecosystem is validated through this service before reaching any downstream system.

## Compliance Rules

| Rule | Standard | Description |
|---|---|---|
| HIPAA | Healthcare | PHI cannot be transmitted without encryption |
| GDPR | Privacy | EU data requires explicit consent |
| EBT | Commerce | Only eligible items can be charged to EBT |
| AML | Finance | Flags transactions >$10K or from sanctioned regions |

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/verify` | POST | Validate a transaction event |
| `/health` | GET | Service health check |

## Tech Stack
- **Language:** Python 3.11
- **Framework:** FastAPI
- **Port:** 8002
