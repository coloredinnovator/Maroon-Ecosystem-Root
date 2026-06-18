# 🌌 Maroon Ecosystem — Sovereign Digital Infrastructure

> **The operating system for Black economic sovereignty.**

[![CI/CD](https://github.com/coloredinnovator/Maroon-Ecosystem-Root/actions/workflows/ci.yml/badge.svg)](https://github.com/coloredinnovator/Maroon-Ecosystem-Root/actions)
[![License](https://img.shields.io/badge/license-Proprietary-maroon)](LICENSE)
[![Version](https://img.shields.io/badge/version-4.0.0-brightgreen)](MAROON_MASTER_CODEX.md)

---

## 🏗️ Architecture Overview

The Maroon Ecosystem is an **18-service sovereign microservices platform** built on a **zero-trust, cryptographically-verified architecture**. Every transaction is hashed via SHA-512 Merkle-DAGs, every event streams to a centralized data lake, and every service is containerized for cloud-native deployment.

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE SOVEREIGN CONTROL PLANE                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Council Core │→ │ Truth-Teller │→ │  Compliance Core     │  │
│  │ (LangGraph)  │  │   (Rust)     │  │ (HIPAA/GDPR/AML)    │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                           ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Palantir Lake (Medallion Lakehouse)          │  │
│  │         Bronze → Silver → Gold + pgvector RAG            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         ↕                    ↕                    ↕
┌────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
│  SOCIAL/MEDIA  │ │    COMMERCE      │ │     HEALTHCARE       │
│ Safe Space     │ │ Maroon Market    │ │ Medical OpCo         │
│ Maroon Tube    │ │ Onita's Market   │ │ Diagnostics (PGx)    │
│ Maroon World   │ │ Market Logistics │ │ Rehab (RTM/IoT)      │
└────────────────┘ └──────────────────┘ └──────────────────────┘
         ↕                    ↕                    ↕
┌────────────────┐ ┌──────────────────┐ ┌──────────────────────┐
│  CIVIC/LEGAL   │ │   INTELLIGENCE   │ │   INFRASTRUCTURE     │
│ PAC Core       │ │ OSINT Swarm      │ │ Sovereign Infra (TF) │
│ Real Estate    │ │ (Scrapy Spiders) │ │ GKE + Cloud SQL      │
│ Law & Finance  │ │                  │ │ BigQuery + GCS       │
└────────────────┘ └──────────────────┘ └──────────────────────┘
```

---

## 📊 Technology Matrix

| Service | Language | Framework | Database | Port |
|---------|----------|-----------|----------|------|
| `maroon-council-core` | Python | FastAPI + LangGraph | — | 8000 |
| `maroon-truth-teller-core` | Rust | Actix-Web | — | 8001 |
| `maroon-compliance-core` | Python | FastAPI | PostgreSQL | 8002 |
| `maroon-palantir-lake` | Python | FastAPI + Kafka | PostgreSQL (pgvector) | 8010 |
| `safe-space-core` | Node.js | Express + Apollo GraphQL | PostgreSQL | 4000 |
| `maroon-tube-core` | Go | net/http + FFmpeg | GCS (HLS) | 8080 |
| `maroon-world-core` | C++ | Godot GDExtension | — | — |
| `maroon-market-core` | TypeScript | MedusaJS | PostgreSQL | 9000 |
| `onitas-market-core` | TypeScript | React + Next.js | — | 3000 |
| `maroon-market-logistics` | Python | FastAPI + OR-Tools | PostgreSQL | 8004 |
| `maroon-medical-opco` | Python | FastAPI + Firebase | Firestore | 8005 |
| `maroon-medical-diagnostics` | Python | FastAPI | PostgreSQL | 8006 |
| `maroon-medical-rehab` | Python | FastAPI | TimescaleDB | 8007 |
| `maroon-pac-core` | Python | FastAPI | PostgreSQL | 8008 |
| `maroon-real-estate-core` | Node.js | Express | PostgreSQL | 8003 |
| `maroon-law-finance-core` | Python | FastAPI | PostgreSQL | 8009 |
| `maroon-osint-swarm` | Python | Scrapy | — | — |
| `maroon-sovereign-infra` | HCL | Terraform | — | — |

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- `gcloud` CLI (for GCP deployment)
- Node.js 20+ (for frontend services)
- Rust toolchain (for Truth-Teller builds)
- Go 1.22+ (for Tube Core builds)

### Local Development

```bash
# Clone the ecosystem
git clone https://github.com/coloredinnovator/Maroon-Ecosystem-Root.git
cd Maroon-Ecosystem-Root

# Bring up the entire ecosystem
docker compose up -d

# Verify all services
curl http://localhost:8000/health   # Council Core
curl http://localhost:8001/health   # Truth-Teller
curl http://localhost:8002/health   # Compliance
curl http://localhost:8010/health   # Palantir Lake
curl http://localhost:4000/health   # Safe Space
curl http://localhost:8080/health   # Tube Core
```

### Individual Service Development

```bash
# Example: Run the Council Core locally
cd maroon-council-core
python -m venv venv && source venv/bin/activate
pip install -r configs/requirements.txt
uvicorn src.main:app --reload --port 8000
```

---

## 🛡️ Security Architecture

- **Zero-Trust**: Every service validates every request. No implicit trust.
- **SHA-512 Merkle-DAGs**: Every state-changing operation produces an immutable cryptographic audit trail via `maroon-truth-teller-core` (Rust).
- **HIPAA/GDPR/AML Compliance**: Enforced at the API gateway level by `maroon-compliance-core` before any transaction touches downstream services.
- **Anonymous Voting**: `maroon-pac-core` uses voter-hash (never voter-ID) for cryptographically private governance.

---

## 📡 The Palantir Mandate

Every repository implements telemetry hooks that stream all events to `maroon-palantir-lake` via Kafka:

```python
def emit_telemetry(source: str, event_type: str, payload: dict):
    producer.send('bronze_raw_ingress', value={
        "source": source,
        "event_type": event_type,
        "data": payload,
        "verification_status": "PENDING_MERKLE_HASH"
    })
```

Data flows through a **Medallion Lakehouse** architecture:
- **Bronze**: Raw ingestion from Kafka
- **Silver**: Cleaned, deduplicated, schema-enforced
- **Gold**: Aggregated analytics, ML feature stores, BI dashboards

---

## ☁️ Cloud Infrastructure (GCP)

Infrastructure is fully codified in Terraform (`maroon-sovereign-infra`):

| Resource | Purpose |
|----------|---------|
| **GKE** | Kubernetes cluster for all containerized services |
| **Cloud SQL** | PostgreSQL 16 with pgvector for embeddings |
| **BigQuery** | Gold-layer analytics and ML feature stores |
| **Cloud Storage** | Media assets, HLS segments, OSINT outputs |
| **Artifact Registry** | Container image storage |
| **VPC** | Private networking with firewall rules |

Environment separation: `dev` → `staging` → `prod`

---

## 📋 Repository Structure (Per Codex §5.2)

Every service follows a standardized layout:

```
service-name/
├── README.md           # Codex-aligned documentation
├── Dockerfile          # Production-ready container
├── src/                # Source code
├── tests/              # Unit and integration tests
├── configs/            # Configuration & dependency files
├── docs/               # Architecture documentation
└── scripts/            # Build, deploy, utility scripts
```

---

## 🏛️ Governance

The Maroon Ecosystem is governed by the [MAROON MASTER CODEX v4.0](MAROON_MASTER_CODEX.md) — a binding specification that dictates all architectural decisions, security protocols, and inter-service communication patterns.

---

## 📞 Contact

**Maroon Technologies**  
[coloredinnovator@maroontechnologies.org](mailto:coloredinnovator@maroontechnologies.org)

---

*Built with sovereign intent. Every line of code traces back to the Codex.*
