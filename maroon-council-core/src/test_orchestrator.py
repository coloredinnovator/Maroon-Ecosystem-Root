import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langchain_core.messages import HumanMessage
from orchestrator.graph import build_orchestrator
from orchestrator.state import OrchestratorState

def run_test():
    app = build_orchestrator()
    
    # Initialize the strict state memory
    initial_state: OrchestratorState = {
        "messages": [HumanMessage(content="Query the baseline demographic data regarding algorithmic mobility and assess risk.")],
        "palantir_context": "",
        "compliance_status": "PENDING",
        "compliance_hash": None,
        "mivl_tier": "TIER_4_FOREIGN_HOSTILE",
        "ledger_cents": 5000,
        "next_node": "",
        "error_message": None
    }
    
    print("\n--- INITIATING MAROON CONTROL PLANE ---")
    
    # Run the graph
    final_state = app.invoke(initial_state)
    
    print("\n--- GRAPH EXECUTION COMPLETE ---")
    print(f"Compliance Hash: {final_state.get('compliance_hash')}")
    print(f"Final Ledger Balance: {final_state.get('ledger_cents')} cents")
    print(f"MIVL Tier: {final_state.get('mivl_tier')}")
    print(f"LLM Response: {final_state['messages'][-1].content}")

if __name__ == "__main__":
    run_test()
