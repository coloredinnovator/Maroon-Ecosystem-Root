from langgraph.graph import StateGraph, END
from orchestrator.state import OrchestratorState
from orchestrator.nodes import gatekeeper_node, palantir_node, financial_node, synthesizer_node
import logging

def build_orchestrator() -> StateGraph:
    """Builds the strict control plane routing graph."""
    logging.info("Compiling the LangGraph Orchestrator...")
    
    workflow = StateGraph(OrchestratorState)
    
    # Add Nodes
    workflow.add_node("gatekeeper", gatekeeper_node)
    workflow.add_node("palantir", palantir_node)
    workflow.add_node("mepp", financial_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    # Entry Point: Always hit the zero-trust gatekeeper first
    workflow.set_entry_point("gatekeeper")
    
    # Conditional Edge from Gatekeeper
    def check_compliance(state: OrchestratorState) -> str:
        if state.get("compliance_status") == "REJECTED":
            logging.error("Compliance Rejected. Terminating graph.")
            return "end"
        return "continue"
        
    workflow.add_conditional_edges(
        "gatekeeper",
        check_compliance,
        {
            "continue": "palantir",
            "end": END
        }
    )
    
    # Sequential Pipeline
    workflow.add_edge("palantir", "mepp")
    workflow.add_edge("mepp", "synthesizer")
    workflow.add_edge("synthesizer", END)
    
    # Compile
    return workflow.compile()
