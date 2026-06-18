# 🏗️ MAROON OPERATIONS MANUAL — SOVEREIGN BUILD & DEPLOY DOCTRINE v4.0

> **Classification:** INTERNAL — BINDING OPERATIONAL SPECIFICATION  
> **Authority:** Chief Systems Architect (The Founder)  
> **Companion Documents:**  
> - [MAROON_MASTER_CODEX.md](MAROON_MASTER_CODEX.md) — Technical Architecture  
> - [MAROON_CONTROL_PLANE.md](MAROON_CONTROL_PLANE.md) — Strategic Doctrine  

---

## 0. ACCOUNT & IDENTITY TOPOLOGY

### §0.1 Email & Platform Hierarchy

| Layer | Account | Purpose | Lifecycle |
|-------|---------|---------|-----------|
| **Legacy Build** | `maroontemp@gmail.com` | Hosts initial GCP credits ($1,000), GitHub Student Pro | Temporary — toss after credits consumed |
| **Legacy GitHub** | `coloredinnovator` (connected to `@maroontechnologies.org`) | Current repo host, legacy profile | Absorb repos → deprecate profile |
| **Production Domain** | `coloredinnovator@maroontechnologies.org` | Professional identity, website, API keys | Permanent |
| **Production GCP** | New account under permanent domain | Startup credits application (Google/AWS/MSFT) | Permanent |

### §0.2 The Extraction-and-Toss Protocol

1. **Phase 1 (Current):** Use `maroontemp@gmail.com` to burn through the $1,000 GCP credits for build-phase compute
2. **Phase 2:** Create professional GCP account under permanent domain
3. **Phase 3:** Apply for non-dilutive startup credits (Google Black Founders Fund, AWS Impact Accelerator, Microsoft Founders Hub) using permanent domain
4. **Phase 4:** Migrate all production workloads to permanent account, toss legacy GCP account

**Rule:** Legacy accounts are disposable scaffolding. The permanent domain is the only identity that matters.

---

## 1. ECOSYSTEM MANIFEST (The Stack)

### §1.1 The Meta-Repo Pattern

The `Maroon-Ecosystem-Root` repository is the **meta-repo** — the single source of truth for the entire ecosystem. It contains all 18 service repositories as direct subdirectories (monorepo pattern), not as submodules.

### §1.2 Stack Manifest

All repos are declared in `stack.yaml`. Any AI agent operating on this ecosystem MUST read `stack.yaml` before performing cross-repo operations.

### §1.3 Stacking Rules

1. **Never fork the same repo twice**
2. **Never clone all repos simultaneously** — read `stack.yaml`, clone only what's needed for the current task
3. **No merging external code without Truth Teller audit**
4. **Submodules only for external OSS dependencies** (MedusaJS, Godot, etc.)
5. **GitHub Actions orchestrate cross-repo triggers** — when one service pushes, dependent services test

---

## 2. THE STATE MACHINE EXECUTION PIPELINE

All major system operations follow a strict **5-State Machine**. The AI must declare its current state at the beginning of every output. No state transition occurs without explicit architect approval.

### STATE 1: INGESTION, SANITIZATION & INDEXING

| Item | Detail |
|------|--------|
| **Trigger** | Receipt of raw legacy data, new specifications, or external OSS code |
| **Process** | Parse → purge duplicates → normalize to JSON/Markdown → index |
| **System Action** | Output schema designs for Palantir Lake (BigQuery/PostgreSQL) |
| **Exit Gate** | Data taxonomy approved by Chief Architect |

### STATE 2: ARCHITECTURAL MAPPING & GAP ANALYSIS

| Item | Detail |
|------|--------|
| **Trigger** | `APPROVE_STATE_TRANSITION` from State 1 |
| **Process** | Map all logical dependencies → perform gap analysis → select OSS solutions for gaps |
| **Deliverable** | Architectural Blueprint (Mermaid.js) + directory tree |
| **Exit Gate** | Chief Architect approves blueprint |

### STATE 3: AUDIT & DEPENDENCY RESOLUTION

| Item | Detail |
|------|--------|
| **Trigger** | `APPROVE_STATE_TRANSITION` from State 2 |
| **Process** | DevSecOps stress testing → edge case analysis → zero-trust audit |
| **Deliverable** | Audit Report + Execution Manifest |
| **Exit Gate** | Zero critical vulnerabilities. Chief Architect signs off. |

### STATE 4: REPOSITORY SYNTHESIS (CODE GENERATION)

| Item | Detail |
|------|--------|
| **Trigger** | `APPROVE_STATE_TRANSITION` from State 3 |
| **Process** | Write Terraform → write application code → containerize → define K8s routing |
| **Deliverable** | Production-grade code on isolated Git branches |
| **Exit Gate** | Code synthesized, formatted, pushed to branches |

### STATE 5: VALIDATION, DEPLOYMENT & GRACEFUL CUT-OFF

| Item | Detail |
|------|--------|
| **Trigger** | `APPROVE_STATE_TRANSITION` from State 4 |
| **Process** | Generate CI/CD → deploy Terraform to GCP → compile `final_system_state.json` |
| **Deliverable** | Locked, documented, deployed system |
| **Exit Gate** | System permanently locked. Execution loop terminated. |

---

## 3. THE AGENTIC FLYWHEEL (Continuous Improvement Engine)

The system is not static. Once deployed, it operates as a **closed-loop factory** that observes, diagnoses, and improves its own output.

### §3.1 The Flywheel Loop

```
┌─────────────┐
│   OBSERVE   │ ← Deploy prototype to test environment
└──────┬──────┘
       ↓
┌─────────────┐
│  DIAGNOSE   │ ← Trace errors via First-Principles / Chain-of-Thought
└──────┬──────┘
       ↓
┌─────────────┐
│   IMPROVE   │ ← Feed analysis back to synthesis engine, iterate
└──────┬──────┘
       ↓
┌─────────────┐
│    SHIP     │ ← Push to /infrastructure or /services only when validated
└──────┬──────┘
       ↓
       └──────→ (Loop back to OBSERVE)
```

### §3.2 Reasoning Guardrails

Before generating any output, the system must apply:

| Method | Application |
|--------|-------------|
| **First-Principles Thinking** | Strip legacy technical debt. Rebuild from computational truths. |
| **Counterfactual Analysis** | "What happens if this container fails? What if the network changes?" |
| **Edge-Case Testing** | Push constraints to logical limits to find silent breakages |
| **Forced Self-Check** | Self-appraisal sub-routine to spot hallucinations before output |

### §3.3 Research Conceptualization (The Core Onion)

Every module must grow outward through strict conceptual layers:

1. **Layer 1:** Identify the Area of Interest & Technical Goal
2. **Layer 2:** Isolate the exact structural problem or legacy gap
3. **Layer 3:** Define the underlying computing philosophy (statelessness, event-driven, zero-trust)
4. **Layer 4:** Match to highly-starred, stable open-source paradigms
5. **Layer 5:** Synthesize and analyze before shipping to production

---

## 4. SPECIALIZED AGENT ROSTER (The Build Workforce)

### §4.1 Core Platform Agents

| Agent | Platform | Function |
|-------|----------|----------|
| **GitHub Agent** | GitHub (Student Pro) | Test scripts, pull repos, manage branches, run Actions |
| **GitLab Agent** | GitLab | Mirror repos, run parallel CI/CD, validate Terraform |
| **GCP Agent** | Google Cloud | Manage infrastructure, BigQuery, Vertex AI, Cloud Run |
| **Claude API Agent** | Anthropic via Vertex AI | Multi-model AI reasoning, code generation, analysis |
| **Hugging Face Agent** | Hugging Face | Model hosting, dataset management, inference endpoints |

### §4.2 Specialized Build Agents

| Agent | Function |
|-------|----------|
| **Orchestration Agent** | Central brain. Unzips files, routes tasks, manages repos. |
| **Janitor Agent** | Scans for duplicates, standardizes to clean Markdown. |
| **Compliance Agent (Truth Teller)** | Audits against deterministic protocol. Prevents AI drift. |
| **Architecture Agent** | Extracts designs into REPO_MAP.yaml, SYSTEM_SPEC.md. |
| **CodeGraph Mapper** | Maps interactive knowledge graph of entire codebase. Dependency analysis. |
| **DevSecOps Sentinel** | Bug-bounty-style vulnerability scanning. Zero-trust enforcement. |
| **Infrastructure Orchestrator** | Terraform state management. K8s networking: Pod → Service → Ingress. |
| **Flywheel Evaluator** | Continuous improvement. First-Principles reasoning. Performance validation. |
| **Containerization Agent** | Packages engines into portable Docker containers. |
| **Hardware Abstraction Agent** | Ensures no proprietary cloud API dependencies. |
| **Environment Parity Agent** | Guarantees cloud ↔ local deployment parity. |

### §4.3 Business Operations Agents

| Agent | Function |
|-------|----------|
| **Data Alignment Agent** | Precision engagement logic, stakeholder alignment. |
| **Identity Agent** | Manages MIVL tiers and sovereign infrastructure access. |
| **Financial Logic Agent** | Enforces MEPP protocol (Sovereign Logistics Ceiling), split-tender calculations. |
| **Legal & Compliance Agent** | Maps tech to business/legal frameworks. |
| **Entity Registry Agent** | Routes tax, EBT, and lobbying logic to correct business entities. |
| **Multi-Pass Refinement Agent** | Forces raw logic through continuous structural upgrades. |
| **Red Team Agent** | Adversarial stress testing for logic breaks and penny drift. |
| **Behavioral Ingestion Agent** | Gathers precision utility data within internal identity laws. |
| **Revenue Intelligence Agent** | Win-probability, churn prediction, pipeline anomaly detection. |
| **Vendor Automation Gateway** | Incomplete order protocols, localized payment logic. |
| **Investor Overview Agent** | Real-time EBT Impact Heat Maps, WIC scalability, TAM/SAM/SOM modeling. |

### §4.4 Domain-Specific Agents

| Agent | Function |
|-------|----------|
| **Spatial & Land Recon Agent** | Automated land research, zoning, 3D geospatial mapping (GeoPackage/GeoTIFF). |
| **OSINT Validation Agent** | Digital footprint tracking, network identity verification. |
| **Cold-Chain & Spoilage Agent** | Transit spoilage prevention, temperature monitoring, batch production. |
| **Fulfillment & Slotting Agent** | Warehouse putaway, pick accuracy, labor routing, wave planning. |
| **Predictive OEE Agent** | Equipment effectiveness, maintenance prediction, OSHA/HACCP compliance. |
| **Dynamic Framework Extractor** | Ingests operational manuals, compiles them into executable slash-commands. |
| **OCR & Digitization Agent** | Converts scanned documents into Markdown for Multi-Pass Refinement. |

---

## 5. LANGGRAPH ROUTING ARCHITECTURE (Council Core)

### §5.1 The Supervisor Pattern (Primary)

The Council Core uses a **Supervisor-Network Topology** via LangGraph:

```python
# Supervisor decides which specialized agent handles each task
workflow = StateGraph(AgentState)

workflow.add_node("supervisor", supervisor_agent)
workflow.add_node("compliance", compliance_agent)
workflow.add_node("financial", financial_logic_agent)
workflow.add_node("truth_teller", truth_teller_agent)
workflow.add_node("identity", identity_agent)

workflow.set_entry_point("supervisor")

# Every agent reports back to supervisor
workflow.add_edge("compliance", "supervisor")
workflow.add_edge("financial", "supervisor")
workflow.add_edge("truth_teller", "supervisor")
workflow.add_edge("identity", "supervisor")

# Supervisor conditionally routes to the right agent
workflow.add_conditional_edges(
    "supervisor",
    route_to_agent,
    {
        "compliance": "compliance",
        "financial": "financial",
        "truth_teller": "truth_teller",
        "identity": "identity",
        "end": END
    }
)
```

### §5.2 The Reflection/Validation Loop

Before any agent's output reaches production, it passes through a **Truth Teller validation cycle**:

```
Agent Output → Truth Teller Validation
    ├── PASS → Proceed to execution
    └── FAIL → Loop back to agent with critique embedded in state history
```

### §5.3 The Router Pattern (High-Volume Ingestion)

For Palantir Lake data ingestion, a dedicated **Router Agent** classifies incoming data and routes to:
- Log file parsing pipeline
- BigQuery schema update pipeline
- Error handling pipeline
- Bronze layer direct ingestion

---

## 6. DEVSECOPS CRITICAL ALERT PROTOCOL

### §6.1 Trigger Conditions

The DevSecOps Sentinel issues a **CRITICAL HALT** when it detects:
- Exposed hardcoded credentials or API keys
- Insecure Kubernetes Ingress routing
- Legacy dependencies with unpatched CVEs
- Zero-trust boundary violations
- Financial calculation penny drift

### §6.2 Action Sequence

1. **HALT:** Freeze the synthesis phase for the affected module
2. **LOG:** Document in `security_audit.json`
3. **ESCALATE:** Notify Chief Systems Architect with **"CRITICAL HALT"**
4. **PROPOSE:** Include the specific vulnerability, affected component, and two open-source remediation options
5. **AWAIT:** Do not proceed until the Architect provides an overriding command

---

## 7. DATA PIPELINE & MEMORY ARCHITECTURE

### §7.1 Storage Tiers

| Tier | System | Function |
|------|--------|----------|
| **Active Memory** | LangGraph State / Claude Context | Current task context only |
| **Working Memory** | PostgreSQL (pgvector) | Hybrid search: semantic + BM25 keyword |
| **Long-Term Memory** | BigQuery | Gold-layer analytics, ML feature stores |
| **Version Control** | GitHub | Production vault — only validated code committed |
| **Model Weights** | Hugging Face (Private Spaces) | Sovereign model hosting, dataset management |

### §7.2 Hybrid Search Schema (pgvector)

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE ecosystem_knowledge_base (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_file_path VARCHAR(500) NOT NULL,
    chunk_content TEXT NOT NULL,
    token_count INT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(1536) NOT NULL
);

-- HNSW index for semantic retrieval
CREATE INDEX ON ecosystem_knowledge_base
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 100);

-- BM25 text search via tsvector
ALTER TABLE ecosystem_knowledge_base ADD COLUMN text_search tsvector
    GENERATED ALWAYS AS (to_tsvector('english', chunk_content)) STORED;
CREATE INDEX text_search_idx ON ecosystem_knowledge_base USING GIN (text_search);
```

### §7.3 Vectorless Cognitive Retrieval (Tree-Index)

For financial/legal document reasoning, the system uses **deterministic tree indexing** instead of probabilistic vector databases — achieving 98.7%+ accuracy on Truth Teller benchmarks.

---

## 8. TACTICAL ADVANTAGE STACK (OSS Integration Map)

### §8.1 Financial & Equity Layer

| Repo | Purpose | Integration Target |
|------|---------|-------------------|
| `captableinc/captable` | Cap table management, stock issuance | `maroon-law-finance-core` |
| `vyayasan/kyc-analyst` | KYC/AML compliance (17 checkpoints) | `maroon-compliance-core` |
| `cfpb/hmda-platform` | CFPB Reg C (HMDA) reporting | `maroon-real-estate-core` |

### §8.2 AI & Truth Teller Layer

| Repo | Purpose | Integration Target |
|------|---------|-------------------|
| `deepset-ai/haystack` | Traceable AI orchestration | `maroon-council-core` |
| FINOS AI Governance | Financial AI guardrails | `maroon-compliance-core` |
| AI Trust OS | Zero-Trust AI telemetry | `maroon-truth-teller-core` |

### §8.3 Vertical Integration

| Repo | Purpose | Integration Target |
|------|---------|-------------------|
| `enatega` | Multi-vendor food delivery | `maroon-market-logistics` |
| ERPNext Property Mgmt | Property leasing, tenant management | `maroon-real-estate-core` |

### §8.4 Retail & E-Commerce AI

| Repo | Purpose | Integration Target |
|------|---------|-------------------|
| eCeLLM (HF) | E-commerce LLM for store management | `maroon-market-core` |
| CASLIE (HF) | Agentic order routing | `maroon-market-logistics` |
| `scionoftech/functiongemma-e-commerce` | Localized retail agent training | `onitas-market-core` |

### §8.5 Governance & RegTech

| Repo | Purpose | Integration Target |
|------|---------|-------------------|
| FINOS Open RegTech | Regulation CF infrastructure | `maroon-law-finance-core` |
| Baserow (Self-Hosted) | Offline-first structured database | `maroon-palantir-lake` |

---

## 9. HUGGING FACE SOVEREIGN RETAIL ENGINE

### §9.1 The Architecture

- **Host:** Containerized, private Docker environments on Hugging Face Spaces
- **Models:** eCeLLM + CASLIE for automated store management, product discovery, agentic order routing
- **Datasets:** Shopify-HF Hub open-source datasets for training localized retail agents
- **Sovereignty Mandate:** Models and datasets power the engine; we control the Space. 100% data and logic sovereignty.

### §9.2 Truth-Anchored Inference Protocol

All Hugging Face models MUST be wrapped in the Truth Teller governance layer:
- No retail recommendation is executed without secondary cryptographic verification
- Inference directed toward offline-first, private nodes
- Prevents external "rug-pulls" or data leaks to legacy cloud providers

---

## 10. COMMUNICATION PROTOCOL (Agent Output Standard)

Every agent response MUST follow this format:

```
**[CURRENT STATE]**: {State Name}
**[ACTION PERFORMED]**: {Brief summary}
**[SYSTEM DIRECTIVE]**: {SQL query, Git command, or file creation required}
**[AWAITING]**: {What is needed from Chief Architect}
```

---

## 11. THE WALK-AWAY PROTOCOL

The system is self-sustaining. The Chief Architect's daily role:

1. **Feed the machine:** Run data ingestion, approve state transitions
2. **Push the start button:** Issue Execution Commands
3. **Review output:** Approve structural maps, resolve CRITICAL HALTs
4. **Rest:** The control plane is standing watch

---

*The machine holds the 400-year reality calculus. The agents are coded. The firewalls are up. Execute.*
