"""
Maroon Law & Finance Core — Legal Document Management & Escrow (v4.0)
Codex §4.4: Contract generation, e-signature workflows,
escrow management for Maroon Market transactions,
regulatory compliance document storage.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import uuid

app = FastAPI(
    title="Maroon Law & Finance Core",
    description="Sovereign Legal Infrastructure — Contracts, Escrow, Compliance",
    version="4.0.0",
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ContractStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_SIGNATURES = "PENDING_SIGNATURES"
    PARTIALLY_SIGNED = "PARTIALLY_SIGNED"
    FULLY_EXECUTED = "FULLY_EXECUTED"
    EXPIRED = "EXPIRED"
    VOIDED = "VOIDED"


class EscrowStatus(str, Enum):
    CREATED = "CREATED"
    FUNDED = "FUNDED"
    RELEASED = "RELEASED"
    DISPUTED = "DISPUTED"
    REFUNDED = "REFUNDED"


class DocumentType(str, Enum):
    CONTRACT = "CONTRACT"
    NDA = "NDA"
    TERMS_OF_SERVICE = "TOS"
    PRIVACY_POLICY = "PRIVACY"
    VENDOR_AGREEMENT = "VENDOR"
    LEASE = "LEASE"
    ESCROW_AGREEMENT = "ESCROW"
    REGULATORY_FILING = "REGULATORY"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class SignatureRecord(BaseModel):
    signer_id: str
    signer_name: str
    signed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    signature_hash: str = ""
    ip_address: Optional[str] = None


class Contract(BaseModel):
    contract_id: str = Field(default_factory=lambda: f"CTR-{str(uuid.uuid4())[:8]}")
    title: str
    document_type: DocumentType
    parties: List[str]
    body_text: str
    status: ContractStatus = ContractStatus.DRAFT
    signatures: List[SignatureRecord] = []
    required_signatures: int = 2
    document_hash: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None


class EscrowAccount(BaseModel):
    escrow_id: str = Field(default_factory=lambda: f"ESC-{str(uuid.uuid4())[:8]}")
    buyer_id: str
    seller_id: str
    amount_usd: float
    contract_id: Optional[str] = None
    status: EscrowStatus = EscrowStatus.CREATED
    funded_at: Optional[str] = None
    released_at: Optional[str] = None
    dispute_reason: Optional[str] = None
    escrow_hash: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EscrowAction(BaseModel):
    action: str   # "fund", "release", "dispute", "refund"
    actor_id: str
    reason: Optional[str] = None


class ComplianceDocument(BaseModel):
    doc_id: str = Field(default_factory=lambda: f"DOC-{str(uuid.uuid4())[:8]}")
    title: str
    document_type: DocumentType
    jurisdiction: str = "US-FEDERAL"
    content_hash: str = ""
    uploaded_by: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expiry_date: Optional[str] = None
    is_active: bool = True


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

def emit_telemetry(event_type: str, payload: dict):
    envelope = {
        "source": "maroon-law-finance-core",
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
        "verification_status": "VERIFIED",
        "merkle_hash": hashlib.sha512(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest(),
    }
    print(f"[Telemetry] {json.dumps(envelope, default=str)}")


def compute_hash(data: str) -> str:
    return hashlib.sha512(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# In-Memory Stores
# ---------------------------------------------------------------------------

_contracts: Dict[str, Contract] = {}
_escrows: Dict[str, EscrowAccount] = {}
_compliance_docs: Dict[str, ComplianceDocument] = {}


# ---------------------------------------------------------------------------
# Contract Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/contracts", status_code=201)
async def create_contract(contract: Contract):
    contract.document_hash = compute_hash(contract.body_text)
    _contracts[contract.contract_id] = contract
    emit_telemetry("contract_created", {"contract_id": contract.contract_id, "type": contract.document_type.value, "parties": len(contract.parties)})
    return {"status": "created", "contract_id": contract.contract_id, "document_hash": contract.document_hash}


@app.get("/api/v1/contracts/{contract_id}")
async def get_contract(contract_id: str):
    if contract_id not in _contracts:
        raise HTTPException(status_code=404, detail="Contract not found")
    return _contracts[contract_id]


@app.get("/api/v1/contracts")
async def list_contracts(status: Optional[ContractStatus] = None, doc_type: Optional[DocumentType] = None):
    contracts = list(_contracts.values())
    if status:
        contracts = [c for c in contracts if c.status == status]
    if doc_type:
        contracts = [c for c in contracts if c.document_type == doc_type]
    return {"contracts": [c.model_dump() for c in contracts]}


@app.post("/api/v1/contracts/{contract_id}/sign")
async def sign_contract(contract_id: str, signer_id: str, signer_name: str):
    """E-signature workflow — adds cryptographic signature to contract."""
    if contract_id not in _contracts:
        raise HTTPException(status_code=404, detail="Contract not found")

    contract = _contracts[contract_id]

    # Check if already signed by this signer
    if any(s.signer_id == signer_id for s in contract.signatures):
        raise HTTPException(status_code=409, detail="Already signed by this party")

    sig_data = f"{contract_id}:{signer_id}:{datetime.now(timezone.utc).isoformat()}"
    sig_hash = compute_hash(sig_data)

    signature = SignatureRecord(signer_id=signer_id, signer_name=signer_name, signature_hash=sig_hash)
    contract.signatures.append(signature)

    if len(contract.signatures) >= contract.required_signatures:
        contract.status = ContractStatus.FULLY_EXECUTED
    elif len(contract.signatures) > 0:
        contract.status = ContractStatus.PARTIALLY_SIGNED

    emit_telemetry("contract_signed", {"contract_id": contract_id, "signer_id": signer_id, "total_signatures": len(contract.signatures)})
    return {"status": contract.status.value, "signature_hash": sig_hash, "total_signatures": len(contract.signatures)}


# ---------------------------------------------------------------------------
# Escrow Endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/escrow", status_code=201)
async def create_escrow(escrow: EscrowAccount):
    escrow.escrow_hash = compute_hash(json.dumps(escrow.model_dump(), sort_keys=True, default=str))
    _escrows[escrow.escrow_id] = escrow
    emit_telemetry("escrow_created", {"escrow_id": escrow.escrow_id, "amount": escrow.amount_usd})
    return {"status": "created", "escrow_id": escrow.escrow_id}


@app.get("/api/v1/escrow/{escrow_id}")
async def get_escrow(escrow_id: str):
    if escrow_id not in _escrows:
        raise HTTPException(status_code=404, detail="Escrow not found")
    return _escrows[escrow_id]


@app.post("/api/v1/escrow/{escrow_id}/action")
async def escrow_action(escrow_id: str, action: EscrowAction):
    """Fund, release, dispute, or refund an escrow account."""
    if escrow_id not in _escrows:
        raise HTTPException(status_code=404, detail="Escrow not found")

    escrow = _escrows[escrow_id]

    if action.action == "fund":
        escrow.status = EscrowStatus.FUNDED
        escrow.funded_at = datetime.now(timezone.utc).isoformat()
    elif action.action == "release":
        if escrow.status != EscrowStatus.FUNDED:
            raise HTTPException(status_code=400, detail="Escrow must be funded before release")
        escrow.status = EscrowStatus.RELEASED
        escrow.released_at = datetime.now(timezone.utc).isoformat()
    elif action.action == "dispute":
        escrow.status = EscrowStatus.DISPUTED
        escrow.dispute_reason = action.reason
    elif action.action == "refund":
        escrow.status = EscrowStatus.REFUNDED
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    emit_telemetry("escrow_action", {"escrow_id": escrow_id, "action": action.action, "actor": action.actor_id})
    return {"status": escrow.status.value, "escrow_id": escrow_id}


# ---------------------------------------------------------------------------
# Compliance Document Storage
# ---------------------------------------------------------------------------

@app.post("/api/v1/compliance/documents", status_code=201)
async def upload_compliance_doc(doc: ComplianceDocument):
    _compliance_docs[doc.doc_id] = doc
    emit_telemetry("compliance_doc_uploaded", {"doc_id": doc.doc_id, "type": doc.document_type.value})
    return {"status": "uploaded", "doc_id": doc.doc_id}


@app.get("/api/v1/compliance/documents")
async def list_compliance_docs(doc_type: Optional[DocumentType] = None, active_only: bool = True):
    docs = list(_compliance_docs.values())
    if doc_type:
        docs = [d for d in docs if d.document_type == doc_type]
    if active_only:
        docs = [d for d in docs if d.is_active]
    return {"documents": [d.model_dump() for d in docs]}


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "maroon-law-finance-core", "version": "4.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
