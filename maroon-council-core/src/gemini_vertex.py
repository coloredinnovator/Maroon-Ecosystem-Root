import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_vertexai import ChatVertexAI

def get_gemini_1_5_pro():
    """
    Initializes the Gemini 1.5 Pro model via Google Cloud Vertex AI.
    This provides massive context window capabilities directly within the GCP sovereign boundary.
    """
    print("[Vertex AI] Initializing Gemini 1.5 Pro API...")
    
    llm = ChatVertexAI(
        model_name="gemini-1.5-pro-001",
        project="maroon-clean-up",
        location="us-central1",
        max_output_tokens=8192,
        temperature=0.2
    )
    return llm

def analyze_ecosystem(llm, codex_content):
    """
    Forces Gemini to process the raw bucket context using its massive token window.
    """
    messages = [
        SystemMessage(content="You are the Maroon Council Core. Analyze the provided codex logic and enforce the architecture directives."),
        HumanMessage(content=f"Here is the master codex logic:\n\n{codex_content}\n\nExecute Phase 1 Analysis.")
    ]
    return llm.invoke(messages)

if __name__ == "__main__":
    print("[Testing] Starting Gemini 1.5 Pro on Vertex AI test run...")
    try:
        gemini_engine = get_gemini_1_5_pro()
        
        # Load the local codex replica
        codex_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "MAROON_MASTER_CODEX.md")
        with open(codex_path, "r", encoding="utf-8") as f:
            codex_content = f.read()
            
        print("[Testing] Master Codex Loaded. Passing to Gemini 1.5 Pro (Vertex AI)...")
        print("[Testing] Waiting for Gemini's analysis...")
        
        result = analyze_ecosystem(gemini_engine, codex_content)
        
        print("\n========================================")
        print("GEMINI 1.5 PRO ANALYSIS COMPLETE:")
        print("========================================")
        print(result.content)
        
    except Exception as e:
        print(f"\n[ERROR] Vertex AI execution failed: {e}")
        print("Make sure you are authenticated with 'gcloud auth application-default login'.")
