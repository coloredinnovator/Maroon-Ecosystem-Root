"""
Maroon Council Core — FastAPI Gateway (v4.0)
Codex §3.1: Entry point for the Multi-Agent Orchestrator.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from orchestrator import run_council_workflow

app = FastAPI(
    title="Maroon Council Core",
    description="Sovereign Multi-Agent Orchestrator — LangGraph Supervisor Network",
    version="4.0.0",
)


class TaskRequest(BaseModel):
    task_id: str
    directive: str
    context: Dict[str, Any] = {}


class TaskResponse(BaseModel):
    status: str
    task_id: str
    decision: str
    truth_hash: str
    compliance_status: str
    financial_breakdown: Dict[str, Any]
    audit_trail: list


@app.post("/api/v1/orchestrate", response_model=TaskResponse)
async def orchestrate_task(request: TaskRequest):
    """
    Entry point for the Maroon Council Orchestrator.
    Routes tasks through: Compliance → Financial Logic → Truth-Teller.
    """
    try:
        result = run_council_workflow(request.directive, request.context)
        return TaskResponse(
            status="success",
            task_id=request.task_id,
            decision=result["final_decision"],
            truth_hash=result["truth_teller_hash"],
            compliance_status=result["compliance_status"],
            financial_breakdown=result.get("financial_breakdown", {}),
            audit_trail=result.get("audit_trail", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "online", "service": "maroon-council-core", "version": "4.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
