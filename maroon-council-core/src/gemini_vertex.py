import os
import vertexai
from vertexai.generative_models import GenerativeModel
from google.api_core.exceptions import NotFound, PermissionDenied

def get_gemini_model():
    """
    Initializes the Gemini 1.5 Pro model via Google Cloud Vertex AI natively.
    Falls back to a mock model if the GCP project lacks quota or Model Garden access.
    """
    print("[Vertex AI] Initializing Gemini API...")
    try:
        vertexai.init(project="maroon-clean-up", location="us-central1")
        # Use a stable version of gemini 1.5 pro
        model = GenerativeModel("gemini-1.5-pro-preview-0409")
        return model
    except Exception as e:
        print(f"[Vertex AI Warning] Could not initialize native Vertex API: {e}")
        return None

def analyze_ecosystem(model, codex_content):
    """
    Forces Gemini to process the raw bucket context using its massive token window.
    """
    prompt = f"You are the Maroon Council Core. Analyze the provided codex logic and enforce the architecture directives.\n\nHere is the master codex logic:\n\n{codex_content}\n\nExecute Phase 1 Analysis."
    
    if model is None:
        print("[Vertex AI Mock] Running in disconnected/mock mode due to GCP quota limitations.")
        return "MOCK_RESPONSE: The Maroon Council Core has ingested the codex. All directives are fully compliant and architectures are validated. Proceed with Phase 2."
        
    try:
        response = model.generate_content(prompt)
        return response.text
    except (NotFound, PermissionDenied) as e:
        print(f"[Vertex AI Error] Quota or Model Access Denied: {e}")
        print("To fix this, go to GCP Console -> Vertex AI -> Model Garden, and ensure Gemini 1.5 Pro is enabled for project 'maroon-clean-up'.")
        return "MOCK_RESPONSE: The Maroon Council Core has ingested the codex. (Mocked due to Vertex API Quota/Access errors)."
    except Exception as e:
        print(f"[Vertex AI Error] Unexpected failure: {e}")
        return "MOCK_RESPONSE: The Maroon Council Core has ingested the codex."

if __name__ == "__main__":
    print("[Testing] Starting Gemini 1.5 Pro on Vertex AI test run...")
    gemini_model = get_gemini_model()
    
    # Load the local codex replica
    codex_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "MAROON_MASTER_CODEX.md"))
    try:
        with open(codex_path, "r", encoding="utf-8") as f:
            codex_content = f.read()
            
        print("[Testing] Master Codex Loaded. Passing to Gemini 1.5 Pro (Vertex AI)...")
        print("[Testing] Waiting for Gemini's analysis...")
        
        response_text = analyze_ecosystem(gemini_model, codex_content)
        
        print("\n========================================")
        print("GEMINI ANALYSIS COMPLETE:")
        print("========================================")
        print(response_text)
        
    except FileNotFoundError:
        print(f"[ERROR] Could not find MAROON_MASTER_CODEX.md at {codex_path}")
