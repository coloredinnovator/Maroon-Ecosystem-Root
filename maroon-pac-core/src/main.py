"""Maroon PAC Core — Cryptographic Voting & Governance API (v4.1)"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone
import hashlib

app = FastAPI(title="Maroon PAC Core", version="4.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_proposals = {}
_votes = []
_voter_hashes = set()

class Proposal(BaseModel):
    proposal_id: str
    title: str
    description: str
    options: list = ["YES", "NO", "ABSTAIN"]

class Vote(BaseModel):
    voter_secret: str  # Hashed, never stored raw
    proposal_id: str
    choice: str

@app.get("/health")
async def health():
    return {"status": "online", "service": "maroon-pac-core", "version": "4.1.0",
            "proposals": len(_proposals), "total_votes": len(_votes)}

@app.get("/")
async def root():
    return {"service": "Maroon PAC Core", "role": "Cryptographic Anonymous Voting + Governance",
            "protocol": "voter_hash (never voter_id) — double-vote prevention via hash dedup", "port": 8008}

@app.post("/api/v1/proposals")
async def create_proposal(req: Proposal):
    _proposals[req.proposal_id] = {**req.model_dump(), "status": "OPEN", "created": datetime.now(timezone.utc).isoformat(),
                                    "tally": {opt: 0 for opt in req.options}}
    return {"status": "created", "proposal": _proposals[req.proposal_id]}

@app.get("/api/v1/proposals")
async def list_proposals():
    return {"count": len(_proposals), "proposals": list(_proposals.values())}

@app.post("/api/v1/vote")
async def cast_vote(req: Vote):
    if req.proposal_id not in _proposals:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal = _proposals[req.proposal_id]
    if proposal["status"] != "OPEN":
        raise HTTPException(status_code=400, detail="Voting is closed")
    voter_hash = hashlib.sha512(req.voter_secret.encode()).hexdigest()[:32]
    dedup_key = f"{voter_hash}:{req.proposal_id}"
    if dedup_key in _voter_hashes:
        raise HTTPException(status_code=409, detail="Double vote detected — voter hash already recorded")
    _voter_hashes.add(dedup_key)
    proposal["tally"][req.choice] = proposal["tally"].get(req.choice, 0) + 1
    vote_record = {"voter_hash": voter_hash, "proposal_id": req.proposal_id, "choice": req.choice,
                   "timestamp": datetime.now(timezone.utc).isoformat(),
                   "receipt": hashlib.sha256(f"{voter_hash}{req.proposal_id}{req.choice}".encode()).hexdigest()[:16]}
    _votes.append(vote_record)
    return {"status": "recorded", "receipt": vote_record["receipt"], "note": "Your identity is cryptographically anonymous"}

@app.get("/api/v1/proposals/{proposal_id}/results")
async def get_results(proposal_id: str):
    if proposal_id not in _proposals:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return {"proposal_id": proposal_id, "tally": _proposals[proposal_id]["tally"],
            "total_votes": sum(_proposals[proposal_id]["tally"].values())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
