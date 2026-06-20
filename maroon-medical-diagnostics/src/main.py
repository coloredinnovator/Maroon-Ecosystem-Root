"""Maroon Medical Diagnostics — PGx/Toxicology Lab API (v4.1)"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone
import hashlib
import json

app = FastAPI(title="Maroon Medical Diagnostics", version="4.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_lab_orders = []

class LabOrder(BaseModel):
    order_id: str
    patient_id: str
    test_type: str  # PGx, TOXICOLOGY, COMPREHENSIVE
    panels: List[str] = []

@app.get("/health")
async def health():
    return {"status": "online", "service": "maroon-medical-diagnostics", "version": "4.1.0",
            "lab_orders": len(_lab_orders), "fhir_version": "R4"}

@app.get("/")
async def root():
    return {"service": "Maroon Medical Diagnostics", "role": "PGx/Toxicology Lab + HL7 FHIR R4",
            "test_types": ["PGx", "TOXICOLOGY", "COMPREHENSIVE"], "port": 8006, "compliance": "HIPAA/CLIA"}

@app.post("/api/v1/orders")
async def create_lab_order(req: LabOrder):
    chain_hash = hashlib.sha256(json.dumps(req.model_dump(), sort_keys=True).encode()).hexdigest()[:16]
    order = {**req.model_dump(), "status": "RECEIVED", "chain_of_custody_hash": chain_hash,
             "created": datetime.now(timezone.utc).isoformat()}
    _lab_orders.append(order)
    return {"status": "created", "order": order}

@app.get("/api/v1/orders")
async def list_orders():
    return {"count": len(_lab_orders), "orders": _lab_orders}

@app.get("/api/v1/panels")
async def list_panels():
    return {"panels": {
        "PGx": ["CYP2D6", "CYP2C19", "CYP3A4", "CYP2C9", "VKORC1", "SLCO1B1"],
        "TOXICOLOGY": ["amphetamines", "opioids", "benzodiazepines", "cannabinoids", "cocaine", "ethanol"],
        "COMPREHENSIVE": ["CBC", "CMP", "lipid_panel", "thyroid", "A1C"]
    }}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
