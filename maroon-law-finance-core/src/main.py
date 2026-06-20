"""Maroon Law & Finance Core — Contracts, Escrow, E-Signatures API (v4.1)"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
import hashlib
import json

app = FastAPI(title="Maroon Law & Finance Core", version="4.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_contracts = {}
_escrows = {}

class ContractCreate(BaseModel):
    contract_id: str
    title: str
    parties: list
    terms: str
    value_cents: int = 0

class EscrowCreate(BaseModel):
    escrow_id: str
    contract_id: str
    amount_cents: int
    payer_id: str
    payee_id: str

@app.get("/health")
async def health():
    return {"status": "online", "service": "maroon-law-finance-core", "version": "4.1.0",
            "contracts": len(_contracts), "escrows": len(_escrows)}

@app.get("/")
async def root():
    return {"service": "Maroon Law & Finance Core", "role": "Contracts, E-Signatures, Escrow Lifecycle",
            "capabilities": ["contract_generation", "e_signatures", "escrow_management", "compliance_docs"], "port": 8009}

@app.post("/api/v1/contracts")
async def create_contract(req: ContractCreate):
    doc_hash = hashlib.sha256(json.dumps(req.model_dump(), sort_keys=True).encode()).hexdigest()[:16]
    contract = {**req.model_dump(), "status": "DRAFT", "document_hash": doc_hash,
                "signatures": [], "created": datetime.now(timezone.utc).isoformat()}
    _contracts[req.contract_id] = contract
    return {"status": "created", "contract": contract}

@app.post("/api/v1/contracts/{contract_id}/sign")
async def sign_contract(contract_id: str, signer_id: str):
    if contract_id not in _contracts:
        raise HTTPException(status_code=404, detail="Contract not found")
    contract = _contracts[contract_id]
    sig_hash = hashlib.sha256(f"{signer_id}{contract_id}{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:16]
    contract["signatures"].append({"signer_id": signer_id, "hash": sig_hash,
                                    "timestamp": datetime.now(timezone.utc).isoformat()})
    if len(contract["signatures"]) >= len(contract["parties"]):
        contract["status"] = "EXECUTED"
    return {"status": "signed", "signature_hash": sig_hash, "contract_status": contract["status"]}

@app.get("/api/v1/contracts")
async def list_contracts():
    return {"count": len(_contracts), "contracts": list(_contracts.values())}

@app.post("/api/v1/escrow")
async def create_escrow(req: EscrowCreate):
    escrow = {**req.model_dump(), "status": "FUNDED", "created": datetime.now(timezone.utc).isoformat()}
    _escrows[req.escrow_id] = escrow
    return {"status": "created", "escrow": escrow}

@app.post("/api/v1/escrow/{escrow_id}/release")
async def release_escrow(escrow_id: str):
    if escrow_id not in _escrows:
        raise HTTPException(status_code=404, detail="Escrow not found")
    _escrows[escrow_id]["status"] = "RELEASED"
    _escrows[escrow_id]["released_at"] = datetime.now(timezone.utc).isoformat()
    return {"status": "released", "escrow": _escrows[escrow_id]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
