# Maroon Market Core

> **Codex Reference:** §4.2 — Shopify-Like Multi-Tenant Commerce Engine

Not just a store — a **sovereign commerce infrastructure** for vendors to build their own storefronts with Split-Tender payment support.

## Features
- **MedusaJS** headless commerce backend
- **Split-Tender Payments:** EBT + Maroon Currency + Fiat
- **Extended Store Entity:** `is_verified_black_owned`, `ebt_eligible`, `governance_hash`
- **Custom Checkout API** with sovereign compliance

## API

| Endpoint | Method | Description |
|---|---|---|
| `/store/checkout` | POST | Execute sovereign split-tender checkout |
| `/health` | GET | Service health check |

## Tech Stack
- **Language:** TypeScript
- **Framework:** MedusaJS
- **Database:** PostgreSQL (via Palantir Lake)
- **Port:** 9000
