"""
Maroon Medical Rehab — Remote Therapeutic Monitoring (RTM) Engine (v4.0)
Codex §4.3: BLE IoT device telemetry ingestion.
Real-time patient vitals dashboard. TimescaleDB for time-series health data.
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
from collections import defaultdict
import hashlib
import json
import uuid

app = FastAPI(
    title="Maroon Medical Rehab",
    description="Sovereign Remote Therapeutic Monitoring — BLE IoT + TimescaleDB",
    version="4.0.0",
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DeviceType(str, Enum):
    HEART_RATE_MONITOR = "HEART_RATE_MONITOR"
    BLOOD_PRESSURE = "BLOOD_PRESSURE"
    PULSE_OXIMETER = "PULSE_OXIMETER"
    GLUCOMETER = "GLUCOMETER"
    GAIT_SENSOR = "GAIT_SENSOR"
    RANGE_OF_MOTION = "RANGE_OF_MOTION"
    PAIN_SCALE = "PAIN_SCALE"
    TEMPERATURE = "TEMPERATURE"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class TherapyType(str, Enum):
    PHYSICAL_THERAPY = "PT"
    OCCUPATIONAL_THERAPY = "OT"
    SPEECH_THERAPY = "ST"
    CARDIAC_REHAB = "CR"
    PULMONARY_REHAB = "PR"
    SUBSTANCE_USE = "SU"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class BleDevice(BaseModel):
    device_id: str = Field(default_factory=lambda: f"BLE-{str(uuid.uuid4())[:8]}")
    device_type: DeviceType
    patient_id: str
    firmware_version: str = "1.0.0"
    battery_level: int = Field(default=100, ge=0, le=100)
    is_paired: bool = True
    last_sync: Optional[str] = None


class VitalReading(BaseModel):
    reading_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    device_id: str
    patient_id: str
    device_type: DeviceType
    value: float
    unit: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = {}


class VitalAlert(BaseModel):
    alert_id: str = Field(default_factory=lambda: f"ALT-{str(uuid.uuid4())[:8]}")
    patient_id: str
    device_type: DeviceType
    severity: AlertSeverity
    message: str
    value: float
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    triggered_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    acknowledged: bool = False


class TherapySession(BaseModel):
    session_id: str = Field(default_factory=lambda: f"SES-{str(uuid.uuid4())[:8]}")
    patient_id: str
    therapy_type: TherapyType
    provider_id: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_minutes: int = 0
    exercises_completed: List[str] = []
    pain_level_start: Optional[int] = Field(default=None, ge=0, le=10)
    pain_level_end: Optional[int] = Field(default=None, ge=0, le=10)
    rom_improvement_degrees: Optional[float] = None
    notes: Optional[str] = None
    status: str = "IN_PROGRESS"


class PatientRtmSummary(BaseModel):
    patient_id: str
    total_readings: int
    active_devices: int
    active_alerts: int
    avg_heart_rate: Optional[float] = None
    last_reading_at: Optional[str] = None
    therapy_sessions_completed: int = 0


# ---------------------------------------------------------------------------
# Telemetry (Palantir Mandate)
# ---------------------------------------------------------------------------

def emit_telemetry(event_type: str, payload: dict):
    envelope = {
        "source": "maroon-medical-rehab",
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
        "verification_status": "PENDING_MERKLE_HASH",
    }
    print(f"[Telemetry] {json.dumps(envelope, default=str)}")


# ---------------------------------------------------------------------------
# Vital Thresholds (Production: configurable per patient)
# ---------------------------------------------------------------------------

THRESHOLDS = {
    DeviceType.HEART_RATE_MONITOR: {"min": 50.0, "max": 120.0, "unit": "bpm"},
    DeviceType.BLOOD_PRESSURE: {"min": 60.0, "max": 180.0, "unit": "mmHg"},
    DeviceType.PULSE_OXIMETER: {"min": 90.0, "max": 100.0, "unit": "%SpO2"},
    DeviceType.GLUCOMETER: {"min": 70.0, "max": 180.0, "unit": "mg/dL"},
    DeviceType.TEMPERATURE: {"min": 96.0, "max": 100.4, "unit": "°F"},
}


# ---------------------------------------------------------------------------
# In-Memory Stores (Production: TimescaleDB)
# ---------------------------------------------------------------------------

_devices: Dict[str, BleDevice] = {}
_readings: List[VitalReading] = []
_alerts: Dict[str, VitalAlert] = {}
_sessions: Dict[str, TherapySession] = {}


# ---------------------------------------------------------------------------
# Alert Engine
# ---------------------------------------------------------------------------

def check_thresholds(reading: VitalReading) -> Optional[VitalAlert]:
    """Check if a vital reading breaches configured thresholds."""
    threshold = THRESHOLDS.get(reading.device_type)
    if not threshold:
        return None

    if reading.value < threshold["min"]:
        return VitalAlert(
            patient_id=reading.patient_id,
            device_type=reading.device_type,
            severity=AlertSeverity.CRITICAL if reading.value < threshold["min"] * 0.85 else AlertSeverity.WARNING,
            message=f"{reading.device_type.value} reading {reading.value} {threshold['unit']} below minimum threshold {threshold['min']}",
            value=reading.value,
            threshold_min=threshold["min"],
        )
    elif reading.value > threshold["max"]:
        return VitalAlert(
            patient_id=reading.patient_id,
            device_type=reading.device_type,
            severity=AlertSeverity.CRITICAL if reading.value > threshold["max"] * 1.15 else AlertSeverity.WARNING,
            message=f"{reading.device_type.value} reading {reading.value} {threshold['unit']} above maximum threshold {threshold['max']}",
            value=reading.value,
            threshold_max=threshold["max"],
        )
    return None


# ---------------------------------------------------------------------------
# API Routes — Devices
# ---------------------------------------------------------------------------

@app.post("/api/v1/devices", status_code=201)
async def register_device(device: BleDevice):
    _devices[device.device_id] = device
    emit_telemetry("ble_device_registered", {"device_id": device.device_id, "type": device.device_type.value, "patient_id": device.patient_id})
    return {"status": "registered", "device_id": device.device_id}


@app.get("/api/v1/devices")
async def list_devices(patient_id: Optional[str] = None):
    devices = list(_devices.values())
    if patient_id:
        devices = [d for d in devices if d.patient_id == patient_id]
    return {"devices": [d.model_dump() for d in devices]}


# ---------------------------------------------------------------------------
# API Routes — Vital Readings (Time-Series Ingestion)
# ---------------------------------------------------------------------------

@app.post("/api/v1/vitals", status_code=201)
async def ingest_vital(reading: VitalReading):
    """Ingest a BLE IoT vital reading and check thresholds."""
    _readings.append(reading)

    # Update device last sync
    if reading.device_id in _devices:
        _devices[reading.device_id].last_sync = reading.timestamp

    # Check thresholds
    alert = check_thresholds(reading)
    if alert:
        _alerts[alert.alert_id] = alert
        emit_telemetry("vital_alert_triggered", {
            "alert_id": alert.alert_id,
            "patient_id": alert.patient_id,
            "severity": alert.severity.value,
            "message": alert.message,
        })

    emit_telemetry("vital_reading_ingested", {
        "device_id": reading.device_id,
        "patient_id": reading.patient_id,
        "type": reading.device_type.value,
        "value": reading.value,
    })
    return {
        "status": "ingested",
        "reading_id": reading.reading_id,
        "alert": alert.model_dump() if alert else None,
    }


@app.get("/api/v1/vitals/{patient_id}")
async def get_patient_vitals(
    patient_id: str,
    device_type: Optional[DeviceType] = None,
    limit: int = Query(default=100, le=1000),
):
    """Get vital readings for a patient (time-series query)."""
    vitals = [r for r in _readings if r.patient_id == patient_id]
    if device_type:
        vitals = [r for r in vitals if r.device_type == device_type]
    vitals = sorted(vitals, key=lambda r: r.timestamp, reverse=True)[:limit]
    return {"readings": [v.model_dump() for v in vitals], "total": len(vitals)}


# ---------------------------------------------------------------------------
# API Routes — Alerts
# ---------------------------------------------------------------------------

@app.get("/api/v1/alerts")
async def list_alerts(patient_id: Optional[str] = None, severity: Optional[AlertSeverity] = None):
    alerts = list(_alerts.values())
    if patient_id:
        alerts = [a for a in alerts if a.patient_id == patient_id]
    if severity:
        alerts = [a for a in alerts if a.severity == severity]
    return {"alerts": [a.model_dump() for a in alerts]}


@app.patch("/api/v1/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    if alert_id not in _alerts:
        raise HTTPException(status_code=404, detail="Alert not found")
    _alerts[alert_id].acknowledged = True
    return {"status": "acknowledged", "alert_id": alert_id}


# ---------------------------------------------------------------------------
# API Routes — Therapy Sessions
# ---------------------------------------------------------------------------

@app.post("/api/v1/sessions", status_code=201)
async def start_session(session: TherapySession):
    _sessions[session.session_id] = session
    emit_telemetry("therapy_session_started", {
        "session_id": session.session_id,
        "patient_id": session.patient_id,
        "therapy_type": session.therapy_type.value,
    })
    return {"status": "started", "session_id": session.session_id}


@app.patch("/api/v1/sessions/{session_id}/complete")
async def complete_session(session_id: str, pain_level_end: Optional[int] = None, rom_improvement: Optional[float] = None):
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    session = _sessions[session_id]
    session.status = "COMPLETED"
    if pain_level_end is not None:
        session.pain_level_end = pain_level_end
    if rom_improvement is not None:
        session.rom_improvement_degrees = rom_improvement
    emit_telemetry("therapy_session_completed", {"session_id": session_id, "pain_improvement": (session.pain_level_start or 0) - (session.pain_level_end or 0)})
    return {"status": "completed", "session_id": session_id}


# ---------------------------------------------------------------------------
# API Routes — RTM Summary Dashboard
# ---------------------------------------------------------------------------

@app.get("/api/v1/summary/{patient_id}", response_model=PatientRtmSummary)
async def get_patient_summary(patient_id: str):
    """Get RTM summary dashboard data for a patient."""
    patient_readings = [r for r in _readings if r.patient_id == patient_id]
    patient_devices = [d for d in _devices.values() if d.patient_id == patient_id and d.is_paired]
    patient_alerts = [a for a in _alerts.values() if a.patient_id == patient_id and not a.acknowledged]
    completed_sessions = [s for s in _sessions.values() if s.patient_id == patient_id and s.status == "COMPLETED"]

    hr_readings = [r.value for r in patient_readings if r.device_type == DeviceType.HEART_RATE_MONITOR]

    return PatientRtmSummary(
        patient_id=patient_id,
        total_readings=len(patient_readings),
        active_devices=len(patient_devices),
        active_alerts=len(patient_alerts),
        avg_heart_rate=round(sum(hr_readings) / len(hr_readings), 1) if hr_readings else None,
        last_reading_at=patient_readings[-1].timestamp if patient_readings else None,
        therapy_sessions_completed=len(completed_sessions),
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "maroon-medical-rehab", "version": "4.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8007)
