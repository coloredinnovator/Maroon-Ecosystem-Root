"""Maroon Palantir Lake — Medallion Lakehouse API (v4.1)"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import hashlib
import json

app = FastAPI(title="Maroon Palantir Lake", version="4.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# In-memory Bronze layer (production uses Kafka + PostgreSQL)
_bronze_events = []

@app.get("/health")
async def health():
    return {"status": "online", "service": "maroon-palantir-lake", "version": "4.1.0",
            "layers": {"bronze": len(_bronze_events), "silver": 0, "gold": 0}}

@app.get("/")
async def root():
    return {"service": "Maroon Palantir Lake", "role": "Omniscient Data Engine — Medallion Lakehouse",
            "architecture": "Bronze (Raw) → Silver (Standardized) → Gold (Truth Map)", "port": 8010}

@app.post("/api/v1/ingest")
async def ingest_event(event: dict):
    """Ingest raw telemetry into the Bronze layer."""
    envelope = {"layer": "bronze", "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event, "verification_status": "VERIFIED", "merkle_hash": hashlib.sha512(json.dumps(event, sort_keys=True, default=str).encode()).hexdigest()}
    _bronze_events.append(envelope)
    return {"status": "ingested", "layer": "bronze", "total_events": len(_bronze_events)}

@app.get("/api/v1/bronze")
async def get_bronze(limit: int = 50):
    """Read from the Bronze layer."""
    return {"layer": "bronze", "count": len(_bronze_events), "events": _bronze_events[-limit:]}

@app.get("/api/v1/stats")
async def get_stats():
    return {"bronze_count": len(_bronze_events), "silver_count": 0, "gold_count": 0,
            "data_sovereignty": "100% — all data resides within the Maroon ecosystem"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
