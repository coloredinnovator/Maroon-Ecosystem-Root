"""
Maroon Medical Rehab — Remote Therapeutic Monitoring (v4.0)
Codex §4.3: BLE IoT device telemetry with TimescaleDB time-series storage.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone
import json

app = FastAPI(title="Maroon Medical Rehab (RTM)", version="4.0.0")

def emit_telemetry(event_type, payload):
    print(f"[Telemetry] {json.dumps({'source': 'maroon-medical-rehab', 'event_type': event_type, 'data': payload})}")

class VitalsReading(BaseModel):
    device_id: str
    patient_id: str
    heart_rate: int
    blood_pressure_systolic: int
    blood_pressure_diastolic: int
    spo2: float
    temperature_f: float
    timestamp: str = ""

class ExerciseSession(BaseModel):
    session_id: str
    patient_id: str
    exercise_type: str  # ROM, STRENGTH, BALANCE, GAIT
    duration_minutes: int
    repetitions: int
    pain_level: int  # 0-10
    compliance_score: float  # 0.0-1.0

_vitals_history = []
_sessions = []

@app.post("/api/v1/vitals")
async def record_vitals(reading: VitalsReading):
    if not reading.timestamp:
        reading.timestamp = datetime.now(timezone.utc).isoformat()
    _vitals_history.append(reading)
    
    # Alert on critical vitals
    alerts = []
    if reading.heart_rate > 120 or reading.heart_rate < 50:
        alerts.append(f"CRITICAL: Heart rate {reading.heart_rate} bpm")
    if reading.spo2 < 92:
        alerts.append(f"CRITICAL: SpO2 {reading.spo2}%")
    
    emit_telemetry("vitals_recorded", {
        "patient_id": reading.patient_id, "device_id": reading.device_id,
        "hr": reading.heart_rate, "spo2": reading.spo2, "alerts": alerts
    })
    return {"status": "recorded", "alerts": alerts}

@app.post("/api/v1/sessions")
async def log_exercise(session: ExerciseSession):
    _sessions.append(session)
    emit_telemetry("exercise_session", {
        "patient_id": session.patient_id, "type": session.exercise_type,
        "compliance": session.compliance_score
    })
    return {"status": "logged", "session_id": session.session_id}

@app.get("/api/v1/vitals/{patient_id}")
async def get_vitals(patient_id: str):
    return [v.model_dump() for v in _vitals_history if v.patient_id == patient_id]

@app.get("/api/v1/dashboard/{patient_id}")
async def patient_dashboard(patient_id: str):
    vitals = [v for v in _vitals_history if v.patient_id == patient_id]
    sessions = [s for s in _sessions if s.patient_id == patient_id]
    avg_compliance = sum(s.compliance_score for s in sessions) / max(len(sessions), 1)
    return {
        "patient_id": patient_id,
        "total_vitals_readings": len(vitals),
        "total_sessions": len(sessions),
        "avg_compliance_score": round(avg_compliance, 2),
        "latest_vitals": vitals[-1].model_dump() if vitals else None,
    }

@app.get("/health")
async def health():
    return {"status": "online", "service": "maroon-medical-rehab", "version": "4.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
