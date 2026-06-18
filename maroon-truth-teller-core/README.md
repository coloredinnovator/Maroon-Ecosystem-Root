# Maroon Truth-Teller Core

> **Codex Reference:** §3.2 — Cryptographic Audit Layer

The immutable cryptographic backbone of the Maroon Ecosystem. Every state-changing operation across all 18 repositories MUST produce a hash through this service.

## Architecture

```
Any Service → POST /api/v1/hash → SHA-512 Receipt
                                       ↓
Multiple Receipts → POST /api/v1/merkle → Merkle-DAG Root (immutable audit)
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/hash` | POST | Hash a JSON payload, return SHA-512 receipt |
| `/api/v1/merkle` | POST | Compute Merkle root from a list of hashes |
| `/health` | GET | Service health check |

### Example: Hash a Payload
```bash
curl -X POST http://localhost:8001/api/v1/hash \
  -H "Content-Type: application/json" \
  -d '{"payload": {"user_id": "M-8891", "action": "EBT_TRANSFER", "amount": 50.00}}'
```

### Example: Compute Merkle Root
```bash
curl -X POST http://localhost:8001/api/v1/merkle \
  -H "Content-Type: application/json" \
  -d '{"hashes": ["abc123...", "def456...", "ghi789..."]}'
```

## Tech Stack
- **Language:** Rust
- **Framework:** Actix-Web 4
- **Crypto:** SHA-512 (sha2 crate)
- **Port:** 8001
