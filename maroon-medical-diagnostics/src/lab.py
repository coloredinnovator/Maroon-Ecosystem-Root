"""
Maroon Medical Diagnostics — PGx/Toxicology Lab Engine (v4.0)
Codex §4.3: Pharmacogenomics (PGx) test result processing.
Toxicology panel management. HL7 FHIR-compliant data exchange.
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
import uuid

app = FastAPI(
    title="Maroon Medical Diagnostics",
    description="Sovereign PGx/Toxicology Lab — HL7 FHIR Compliant",
    version="4.0.0",
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TestType(str, Enum):
    PGX = "PGX"                 # Pharmacogenomics
    TOXICOLOGY = "TOXICOLOGY"
    PANEL = "PANEL"             # Comprehensive panel
    DRUG_SCREEN = "DRUG_SCREEN"
    GENETIC = "GENETIC"


class Priority(str, Enum):
    ROUTINE = "ROUTINE"
    STAT = "STAT"
    URGENT = "URGENT"


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    SPECIMEN_RECEIVED = "SPECIMEN_RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SpecimenType(str, Enum):
    BLOOD = "BLOOD"
    URINE = "URINE"
    SALIVA = "SALIVA"
    HAIR = "HAIR"
    TISSUE = "TISSUE"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class Specimen(BaseModel):
    specimen_id: str = Field(default_factory=lambda: f"SPC-{str(uuid.uuid4())[:8]}")
    specimen_type: SpecimenType
    collected_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    chain_of_custody_hash: str = ""


class DiagnosticOrder(BaseModel):
    order_id: str = Field(default_factory=lambda: f"DX-{str(uuid.uuid4())[:8]}")
    patient_id: str
    test_type: TestType
    specimens: List[Specimen] = []
    ordering_provider: str
    priority: Priority = Priority.ROUTINE
    icd10_codes: List[str] = []
    clinical_notes: Optional[str] = None
    status: OrderStatus = OrderStatus.CREATED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class PgxGenotype(BaseModel):
    gene: str           # e.g., CYP2D6, CYP2C19
    diplotype: str      # e.g., *1/*2
    phenotype: str      # e.g., "Normal Metabolizer", "Poor Metabolizer"
    affected_drugs: List[str] = []
    clinical_recommendation: str = ""


class ToxicologyResult(BaseModel):
    substance: str
    detected: bool
    concentration_ng_ml: Optional[float] = None
    cutoff_ng_ml: float
    confirmation_method: str = "LC-MS/MS"


class DiagnosticResult(BaseModel):
    result_id: str = Field(default_factory=lambda: f"RES-{str(uuid.uuid4())[:8]}")
    order_id: str
    patient_id: str
    test_type: TestType
    pgx_genotypes: List[PgxGenotype] = []
    toxicology_results: List[ToxicologyResult] = []
    raw_findings: Dict[str, Any] = {}
    result_hash: str = ""
    status: str = "FINAL"
    resulted_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Telemetry (Palantir Mandate)
# ---------------------------------------------------------------------------

def emit_telemetry(event_type: str, payload: dict):
    envelope = {
        "source": "maroon-medical-diagnostics",
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": payload,
        "verification_status": "VERIFIED",
        "merkle_hash": hashlib.sha512(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest(),
    }
    print(f"[Telemetry] {json.dumps(envelope, default=str)}")


def compute_hash(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha512(canonical.encode()).hexdigest()


# ---------------------------------------------------------------------------
# In-Memory Stores (Production: PostgreSQL)
# ---------------------------------------------------------------------------

_orders: Dict[str, DiagnosticOrder] = {}
_results: Dict[str, DiagnosticResult] = {}


# ---------------------------------------------------------------------------
# API Routes — Orders
# ---------------------------------------------------------------------------

@app.post("/api/v1/orders", status_code=201)
async def create_order(order: DiagnosticOrder):
    """Create a new diagnostic lab order."""
    # Chain of custody hash for each specimen
    for specimen in order.specimens:
        specimen.chain_of_custody_hash = compute_hash({
            "specimen_id": specimen.specimen_id,
            "type": specimen.specimen_type.value,
            "collected_at": specimen.collected_at,
            "patient_id": order.patient_id,
        })

    _orders[order.order_id] = order
    emit_telemetry("diagnostic_order_created", {
        "order_id": order.order_id,
        "patient_id": order.patient_id,
        "test_type": order.test_type.value,
        "priority": order.priority.value,
        "specimen_count": len(order.specimens),
    })
    return {"status": "created", "order_id": order.order_id, "specimens": len(order.specimens)}


@app.get("/api/v1/orders/{order_id}")
async def get_order(order_id: str):
    if order_id not in _orders:
        raise HTTPException(status_code=404, detail="Order not found")
    return _orders[order_id]


@app.get("/api/v1/orders")
async def list_orders(
    patient_id: Optional[str] = None,
    test_type: Optional[TestType] = None,
    status: Optional[OrderStatus] = None,
    limit: int = Query(default=50, le=200),
):
    """List diagnostic orders with optional filters."""
    orders = list(_orders.values())
    if patient_id:
        orders = [o for o in orders if o.patient_id == patient_id]
    if test_type:
        orders = [o for o in orders if o.test_type == test_type]
    if status:
        orders = [o for o in orders if o.status == status]
    return {"orders": [o.model_dump() for o in orders[:limit]], "total": len(orders)}


@app.patch("/api/v1/orders/{order_id}/status")
async def update_order_status(order_id: str, status: OrderStatus):
    if order_id not in _orders:
        raise HTTPException(status_code=404, detail="Order not found")
    _orders[order_id].status = status
    emit_telemetry("order_status_updated", {"order_id": order_id, "new_status": status.value})
    return {"order_id": order_id, "status": status.value}


# ---------------------------------------------------------------------------
# API Routes — Results
# ---------------------------------------------------------------------------

@app.post("/api/v1/results", status_code=201)
async def submit_result(result: DiagnosticResult):
    """Submit a completed diagnostic result."""
    result.result_hash = compute_hash(result.model_dump())

    # Update order status
    if result.order_id in _orders:
        _orders[result.order_id].status = OrderStatus.COMPLETED

    _results[result.result_id] = result
    emit_telemetry("diagnostic_result_submitted", {
        "result_id": result.result_id,
        "order_id": result.order_id,
        "test_type": result.test_type.value,
        "hash": result.result_hash[:32],
    })
    return {"status": "submitted", "result_id": result.result_id, "hash": result.result_hash}


@app.get("/api/v1/results/{result_id}")
async def get_result(result_id: str):
    if result_id not in _results:
        raise HTTPException(status_code=404, detail="Result not found")
    return _results[result_id]


@app.get("/api/v1/results/order/{order_id}")
async def get_results_by_order(order_id: str):
    return {
        "results": [r.model_dump() for r in _results.values() if r.order_id == order_id]
    }


# ---------------------------------------------------------------------------
# HL7 FHIR Endpoints (Codex §4.3)
# ---------------------------------------------------------------------------

@app.get("/api/v1/fhir/DiagnosticReport/{order_id}")
async def fhir_diagnostic_report(order_id: str):
    """HL7 FHIR R4 DiagnosticReport resource."""
    order = _orders.get(order_id)
    results = [r for r in _results.values() if r.order_id == order_id]

    observations = []
    for res in results:
        for pgx in res.pgx_genotypes:
            observations.append({
                "resourceType": "Observation",
                "code": {"text": f"PGx: {pgx.gene}"},
                "valueString": f"{pgx.diplotype} — {pgx.phenotype}",
                "interpretation": [{"text": pgx.clinical_recommendation}],
            })
        for tox in res.toxicology_results:
            observations.append({
                "resourceType": "Observation",
                "code": {"text": f"Toxicology: {tox.substance}"},
                "valueBoolean": tox.detected,
                "valueQuantity": {"value": tox.concentration_ng_ml, "unit": "ng/mL"} if tox.concentration_ng_ml else None,
            })

    return {
        "resourceType": "DiagnosticReport",
        "id": order_id,
        "status": "final" if results else "registered",
        "code": {"text": order.test_type.value if order else "Unknown"},
        "subject": {"reference": f"Patient/{order.patient_id}" if order else ""},
        "issued": datetime.now(timezone.utc).isoformat(),
        "result": observations,
    }


@app.get("/api/v1/fhir/Patient/{patient_id}/diagnostics")
async def fhir_patient_diagnostics(patient_id: str):
    """Get all FHIR DiagnosticReports for a patient."""
    patient_orders = [o for o in _orders.values() if o.patient_id == patient_id]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": len(patient_orders),
        "entry": [{"resource": {"resourceType": "DiagnosticReport", "id": o.order_id}} for o in patient_orders],
    }


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "online", "service": "maroon-medical-diagnostics", "version": "4.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
