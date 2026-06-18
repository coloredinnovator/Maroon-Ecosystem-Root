# Maroon Council Core

> **Codex Reference:** §3.1 — The Sovereign Control Plane (The Brain)

The Multi-Agent Orchestrator for the Maroon Ecosystem. Uses a **LangGraph Supervisor-Network Topology** to route every directive through three specialized agents before execution.

## Architecture

```
Directive → [Compliance Agent] → [Financial Logic Agent] → [Truth-Teller Agent] → Decision
                                                                    ↓
                                                            Palantir Lake (Telemetry)
```

## Agents

| Agent | Function | Codex Section |
|---|---|---|
| **Compliance Agent** | HIPAA, GDPR, EBT, AML guardrails | §3.3 |
| **Financial Logic Agent** | Split-Tender payment allocation | §4.2 |
| **Truth-Teller Agent** | SHA-512 cryptographic state hash | §3.2 |

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/orchestrate` | POST | Submit a directive for multi-agent processing |
| `/health` | GET | Service health check |

## Running

```bash
# Docker
docker build -t maroon-council-core .
docker run -p 8000:8000 maroon-council-core

# Local
pip install -r configs/requirements.txt
uvicorn src.main:app --port 8000
```

## Tech Stack
- **Language:** Python 3.11
- **Framework:** FastAPI + LangGraph
- **Port:** 8000
