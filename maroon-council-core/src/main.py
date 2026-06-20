"""
Maroon Council Core — FastAPI Gateway (v5.0 - NASA Grade)
Codex §3.1: Entry point for the Multi-Agent Orchestrator.

Exposes:
  - /api/v1/orchestrate    — LangGraph Supervisor pipeline
  - /api/v1/identity/*     — MIVL Identity Verification Layer
  - /api/v1/tender         — MEPP Split-Tender Engine
  - /api/v1/cookout        — Cookout Protocol Trust Gateway
  - /health                — Standard health check
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from mivl import (
    MIVLIdentity, MIVLTier, CookoutProtocol, TIER_ACCESS,
    IdentityError, TierUpgradeError, CryptographicAnomaly
)
from mepp import (
    split_tender, enforce_rls_cap, to_dollars,
    SOVEREIGN_LOGISTICS_CEILING_CENTS, RLS_MONTHLY_CAP_CENTS,
    CartItem, MEPPBaseException, PennyDriftError, SovereignLogisticsViolation, InvalidCurrencyFormat
)

app = FastAPI(
    title="Maroon Council Core",
    description="Sovereign Multi-Agent Orchestrator — The Brain of the Maroon Ecosystem",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global Exception Handlers (NASA Grade)
# ---------------------------------------------------------------------------
@app.exception_handler(IdentityError)
async def identity_error_handler(request: Request, exc: IdentityError):
    return JSONResponse(status_code=403, content={"detail": str(exc), "code": "MIVL_VIOLATION"})

@app.exception_handler(MEPPBaseException)
async def mepp_error_handler(request: Request, exc: MEPPBaseException):
    status_code = 400
    if isinstance(exc, PennyDriftError):
        status_code = 422
    return JSONResponse(status_code=status_code, content={"detail": str(exc), "code": "MEPP_VIOLATION"})

# ---------------------------------------------------------------------------
# In-memory identity store
# ---------------------------------------------------------------------------
_identities: Dict[str, MIVLIdentity] = {}

# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------

class TaskRequest(BaseModel):
    task_id: str
    directive: str
    context: Dict[str, Any] = {}

class TaskResponse(BaseModel):
    status: str
    task_id: str
    decision: str
    truth_hash: str
    compliance_status: str
    financial_breakdown: Dict[str, Any]
    audit_trail: list

class IdentityCreateRequest(BaseModel):
    entity_id: str
    display_name: str = ""

class TierUpgradeRequest(BaseModel):
    entity_id: str
    new_tier: int
    reason: str

class VoucherRequest(BaseModel):
    entity_id: str
    voucher_entity_id: str
    voucher_tier: int

class CookoutRequest(BaseModel):
    has_vouching_chain: bool
    historical_intent_verified: bool
    contribution_value: float
    contribution_threshold: float = 0.0

class SplitTenderRequest(BaseModel):
    items: List[CartItem]
    delivery_fee: float = 0.0
    platform_fee: float = 0.0
    maroon_bucks_available: float = 0.0
    has_ebt: bool = False

class RLSCapRequest(BaseModel):
    vendor_id: str
    current_month_fees_cents: int
    proposed_fee_cents: int


# ---------------------------------------------------------------------------
# Health & Status
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": "maroon-council-core",
        "version": "5.0.0",
        "engines": {
            "orchestrator": "active",
            "mivl": "active",
            "mepp": "active",
        },
        "sovereign_logistics_ceiling_cents": SOVEREIGN_LOGISTICS_CEILING_CENTS,
        "rls_monthly_cap_cents": RLS_MONTHLY_CAP_CENTS,
        "identities_registered": len(_identities),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/")
async def root():
    return {"name": "Maroon Council Core", "version": "5.0.0"}


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

@app.post("/api/v1/orchestrate", response_model=TaskResponse)
async def orchestrate_task(request: TaskRequest):
    try:
        from orchestrator import run_council_workflow
        result = run_council_workflow(request.directive, request.context)
        return TaskResponse(
            status="success",
            task_id=request.task_id,
            decision=result["final_decision"],
            truth_hash=result["truth_teller_hash"],
            compliance_status=result["compliance_status"],
            financial_breakdown=result.get("financial_breakdown", {}),
            audit_trail=result.get("audit_trail", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# MIVL Identity
# ---------------------------------------------------------------------------

@app.post("/api/v1/identity/create")
async def create_identity(request: IdentityCreateRequest):
    if request.entity_id in _identities:
        raise HTTPException(status_code=409, detail="Entity already exists")
    identity = MIVLIdentity(entity_id=request.entity_id, display_name=request.display_name)
    _identities[request.entity_id] = identity
    return {"status": "created", "identity": identity.model_dump()}

@app.get("/api/v1/identity/{entity_id}")
async def get_identity(entity_id: str):
    if entity_id not in _identities:
        raise HTTPException(status_code=404, detail="Entity not found")
    return _identities[entity_id].model_dump()

@app.post("/api/v1/identity/upgrade")
async def upgrade_tier(request: TierUpgradeRequest):
    if request.entity_id not in _identities:
        raise HTTPException(status_code=404, detail="Entity not found")
    identity = _identities[request.entity_id]
    record = identity.upgrade_tier(MIVLTier(request.new_tier), request.reason)
    return {"status": "upgraded", "record": record.model_dump(), "identity": identity.model_dump()}

@app.post("/api/v1/identity/vouch")
async def vouch_for_entity(request: VoucherRequest):
    if request.entity_id not in _identities:
        raise HTTPException(status_code=404, detail="Entity not found")
    identity = _identities[request.entity_id]
    identity.add_voucher(request.voucher_entity_id, MIVLTier(request.voucher_tier))
    return {"status": "vouched", "identity": identity.model_dump()}

@app.post("/api/v1/identity/flag-anomaly")
async def flag_anomaly(entity_id: str, anomaly_type: str, details: str):
    if entity_id not in _identities:
        raise HTTPException(status_code=404, detail="Entity not found")
    identity = _identities[entity_id]
    flag = identity.flag_anomaly(anomaly_type, details)
    return {"status": "flagged", "anomaly": flag.model_dump(), "identity": identity.model_dump()}

@app.get("/api/v1/identity/{entity_id}/access/{permission}")
async def check_access(entity_id: str, permission: str):
    if entity_id not in _identities:
        raise HTTPException(status_code=404, detail="Entity not found")
    identity = _identities[entity_id]
    return {
        "entity_id": entity_id,
        "permission": permission,
        "granted": permission in identity.permissions,
        "tier": identity.tier.name,
        "trust_score": identity.trust_score,
    }

# ---------------------------------------------------------------------------
# Cookout Protocol
# ---------------------------------------------------------------------------

@app.post("/api/v1/cookout")
async def run_cookout_protocol(request: CookoutRequest):
    result = CookoutProtocol.evaluate(
        has_vouching_chain=request.has_vouching_chain,
        historical_intent_verified=request.historical_intent_verified,
        contribution_value=request.contribution_value,
        threshold=request.contribution_threshold,
    )
    return result.model_dump()


# ---------------------------------------------------------------------------
# MEPP Split-Tender
# ---------------------------------------------------------------------------

@app.post("/api/v1/tender")
async def run_split_tender(request: SplitTenderRequest):
    result = split_tender(
        items=request.items,
        delivery_fee_dollars=request.delivery_fee,
        platform_fee_dollars=request.platform_fee,
        maroon_bucks_available_dollars=request.maroon_bucks_available,
        has_ebt=request.has_ebt,
    )
    return result.model_dump()

@app.post("/api/v1/rls-cap")
async def run_rls_cap(request: RLSCapRequest):
    result = enforce_rls_cap(
        vendor_id=request.vendor_id,
        current_month_fees_cents=request.current_month_fees_cents,
        proposed_fee_cents=request.proposed_fee_cents,
    )
    return result.model_dump()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
