import httpx
import logging
import os
import chromadb
from langchain_core.messages import AIMessage
from orchestrator.state import OrchestratorState

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] [Nodes] %(message)s')

def gatekeeper_node(state: OrchestratorState) -> OrchestratorState:
    """Zero-Trust Gatekeeper Validation."""
    logging.info("Routing to Compliance Gatekeeper...")
    try:
        # Hitting the standalone Maroon Compliance Core microservice
        response = httpx.post("http://localhost:8002/api/v1/verify", json={
            "user_id": "api@maroontechnologies.org",
            "action_type": "ORCHESTRATOR_QUERY",
            "amount": 0.0,
            "contains_phi": False,
            "data_region": "US"
        }, timeout=5.0)
        
        if response.status_code == 200:
            data = response.json()
            state["compliance_status"] = "APPROVED"
            state["compliance_hash"] = data.get("audit_hash")
            logging.info(f"Compliance APPROVED: {state['compliance_hash']}")
        else:
            state["compliance_status"] = "REJECTED"
            state["error_message"] = "Compliance Core rejected the transaction."
            
    except Exception as e:
        logging.error(f"Gatekeeper failed: {e}")
        state["compliance_status"] = "REJECTED"
        state["error_message"] = "Connection to Compliance Core severed."

    return state

def palantir_node(state: OrchestratorState) -> OrchestratorState:
    """Semantic Retrieval from the 400-Year Vector Lake."""
    logging.info("Querying Palantir Lake...")
    
    # In production, this hits the palantir-lake microservice API.
    # Here, we directly query the Silver Layer ChromaDB for extreme performance.
    silver_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                              "..", "maroon-palantir-lake", "data", "silver_vectors")
    
    # Fallback context if ChromaDB isn't accessible or is empty
    context = "System Default: 400-year historical baseline dictates zero-trust algorithmic assumptions."
    
    try:
        if os.path.exists(silver_dir):
            client = chromadb.PersistentClient(path=silver_dir)
            collection = client.get_collection("palantir_lake_silver")
            
            # Extract the user's latest query
            query = state["messages"][-1].content
            
            results = collection.query(
                query_texts=[query],
                n_results=3
            )
            
            if results["documents"] and results["documents"][0]:
                context = "\n".join(results["documents"][0])
                logging.info("Palantir extraction successful.")
    except Exception as e:
        logging.warning(f"Palantir Vector Lake query failed, using fallback context. Error: {e}")

    state["palantir_context"] = context
    return state

def financial_node(state: OrchestratorState) -> OrchestratorState:
    """Interacts with MEPP/MIVL mathematical engine."""
    logging.info("Hitting MEPP Engine...")
    try:
        # In this prototype, we simulate the internal MEPP call
        # A real integration would POST to http://localhost:8000/process-transaction
        state["ledger_cents"] -= 50 # Deduct 50 cents processing fee
        state["mivl_tier"] = "TIER_2_HOSTILE_TRANSACTIONAL"
    except Exception as e:
        logging.error(f"MEPP Math failed: {e}")
    
    return state

def synthesizer_node(state: OrchestratorState) -> OrchestratorState:
    """The Vertex AI Brain that reasons over the entire ecosystem."""
    logging.info("Synthesizing Final Output via Vertex AI...")
    
    # NOTE: To run this locally without ADC credentials, we use a mock AI for structural proof, 
    # but the architecture is strictly typed for ChatVertexAI.
    try:
        # model = ChatVertexAI(model_name="gemini-1.5-pro-preview-0409")
        # response = model.invoke(prompt)
        
        _ = (
            f"You are the Maroon Control Plane. "
            f"Context from Palantir: {state['palantir_context']}\n"
            f"Ledger: {state['ledger_cents']} cents\n"
            f"Compliance: {state['compliance_hash']}"
        )
        
        # Simulating LLM response based on context
        bot_response = f"NASA-Grade Orchestrator Active. Gatekeeper hash generated: {state['compliance_hash']}. Retrieved Palantir knowledge. Remaining balance: {state['ledger_cents']} cents. Response: Acknowledged."
        
        state["messages"].append(AIMessage(content=bot_response))
    except Exception as e:
        state["error_message"] = str(e)
        
    return state
