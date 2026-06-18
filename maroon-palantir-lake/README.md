# Maroon Palantir Lake

> **Codex Reference:** §3.4 — Omniscient Data Engine

The centralized intelligence backbone. Every telemetry event, user action, and transaction across all 18 repositories flows through this service.

## Architecture: Medallion Lakehouse

```
All Services → Kafka → [Bronze: Raw] → [Silver: Cleaned] → [Gold: Aggregated]
                                              ↓
                                    PostgreSQL (pgvector) → GraphRAG
```

| Layer | Description |
|---|---|
| **Bronze** | Raw ingestion from Kafka. Immutable landing zone. |
| **Silver** | Deduplicated, schema-validated, quality-scored records. |
| **Gold** | Aggregated analytics, ML feature stores, BI views. |

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/ingest` | POST | Ingest a raw event into Bronze |
| `/api/v1/process/silver` | POST | Transform Bronze → Silver |
| `/api/v1/schema` | GET | Return the full DDL schema |
| `/health` | GET | Service health check |

## Tech Stack
- **Language:** Python 3.11
- **Framework:** FastAPI + PySpark + Kafka
- **Database:** PostgreSQL (pgvector)
- **Port:** 8010
