"""Maroon Medical Rehab — RTM IoT Vitals API (v4.1)"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timezone

app = FastAPI(title="Maroon Medical Rehab", version="4.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_vitals = []
_alerts = []

class VitalReading(BaseModel):
    device_id: str
    patient_id: str
    heart_rate: float = 0
    blood_pressure_sys: float = 0
    blood_pressure_dia: float = 0
    spo2: float = 0
    temperature: float = 0

THRESHOLDS = {"heart_rate": (50, 120), "spo2": (90, 100), "temperature": (96.0, 100.4),
              "blood_pressure_sys": (90, 140), "blood_pressure_dia": (60, 90)}

@app.get("/health")
async def health():
    return {"status": "online", "service": "maroon-medical-rehab", "version": "4.1.0",
            "vitals_count": len(_vitals), "active_alerts": len([a for a in _alerts if a["status"] == "ACTIVE"])}

@app.get("/")
async def root():
    return {"service": "Maroon Medical Rehab", "role": "RTM with BLE IoT Vitals + Threshold Alerts",
            "capabilities": ["BLE_device_ingestion", "vital_thresholds", "alert_dispatch", "therapy_sessions"], "port": 8007}

@app.post("/api/v1/vitals")
async def ingest_vitals(req: VitalReading):
    reading = {**req.model_dump(), "timestamp": datetime.now(timezone.utc).isoformat()}
    _vitals.append(reading)
    triggered = []
    for metric, (low, high) in THRESHOLDS.items():
        val = getattr(req, metric, 0)
        if val > 0 and (val < low or val > high):
            alert = {"patient_id": req.patient_id, "device_id": req.device_id, "metric": metric,
                     "value": val, "range": f"{low}-{high}", "status": "ACTIVE",
                     "timestamp": datetime.now(timezone.utc).isoformat()}
            _alerts.append(alert)
            triggered.append(alert)
    return {"status": "recorded", "alerts_triggered": len(triggered), "alerts": triggered}

@app.get("/api/v1/vitals")
async def get_vitals(patient_id: str = None, limit: int = 50):
    data = [v for v in _vitals if not patient_id or v["patient_id"] == patient_id]
    return {"count": len(data), "vitals": data[-limit:]}

@app.get("/api/v1/alerts")
async def get_alerts():
    return {"count": len(_alerts), "alerts": _alerts}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
