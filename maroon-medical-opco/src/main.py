"""Maroon Medical OpCo — Patient Management API (v4.1)"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone

app = FastAPI(title="Maroon Medical OpCo", version="4.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_patients = {}
_dispatches = []

class PatientCreate(BaseModel):
    patient_id: str
    name: str
    dob: str
    service_line: str = "MIH"  # MIH, SNF, PPECC, HOME_HEALTH

@app.get("/health")
async def health():
    return {"status": "online", "service": "maroon-medical-opco", "version": "4.1.0",
            "patients": len(_patients), "active_dispatches": len(_dispatches)}

@app.get("/")
async def root():
    return {"service": "Maroon Medical OpCo", "role": "MIH/SNF/PPECC Patient Management + Care Dispatch",
            "service_lines": ["MIH", "SNF", "PPECC", "HOME_HEALTH"], "port": 8005, "compliance": "HIPAA"}

@app.post("/api/v1/patients")
async def register_patient(req: PatientCreate):
    _patients[req.patient_id] = {"id": req.patient_id, "name": req.name, "dob": req.dob,
                                  "service_line": req.service_line, "created": datetime.now(timezone.utc).isoformat()}
    return {"status": "registered", "patient": _patients[req.patient_id]}

@app.get("/api/v1/patients")
async def list_patients():
    return {"count": len(_patients), "patients": list(_patients.values())}

@app.post("/api/v1/dispatch")
async def create_dispatch(patient_id: str, provider_id: str, service_type: str = "MIH"):
    dispatch = {"id": f"D-{len(_dispatches)+1:04d}", "patient_id": patient_id, "provider_id": provider_id,
                "service_type": service_type, "status": "DISPATCHED", "timestamp": datetime.now(timezone.utc).isoformat()}
    _dispatches.append(dispatch)
    return dispatch

@app.get("/api/v1/dispatches")
async def list_dispatches():
    return {"count": len(_dispatches), "dispatches": _dispatches}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
