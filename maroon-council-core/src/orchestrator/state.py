from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class OrchestratorState(TypedDict):
    """
    The strict cognitive memory for the Maroon Control Plane.
    This dictates exactly what the graph remembers during execution.
    """
    messages: List[BaseMessage]
    
    # Context retrieved from the Palantir Lake Vector DB
    palantir_context: str
    
    # Zero-Trust Validation
    compliance_status: str # "PENDING", "APPROVED", "REJECTED"
    compliance_hash: Optional[str]
    
    # Financial/Identity State from Council Core
    mivl_tier: str
    ledger_cents: int
    
    # Meta execution routing
    next_node: str
    error_message: Optional[str]
