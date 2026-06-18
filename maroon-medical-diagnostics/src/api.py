from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Maroon Medical Diagnostics API")

class LabResult(BaseModel):
    patient_id: str
    test_type: str
    pgx_marker: str
    risk_level: str

@app.post("/api/v1/lab/submit")
async def submit_lab_result(result: LabResult):
    print(f"[Diagnostics] Processing {result.test_type} for {result.patient_id}")
    # Forward data to BigQuery for long-term analytics and Maroon Palantir
    return {"status": "success", "message": "Result processed and routed to BigQuery."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
