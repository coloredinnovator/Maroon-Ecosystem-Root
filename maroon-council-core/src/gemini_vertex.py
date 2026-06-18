"""
Maroon Council Core — Multi-Model AI Integration (v4.0)
Codex §3.1: LLM Backend — Gemini 1.5 Pro via Vertex AI (primary)
with Claude Opus 4.8 as secondary when quota allows.

Supports:
  1. Google Vertex AI (Gemini) — native Python SDK
  2. Anthropic Claude via Vertex AI — REST API
  3. Mock fallback for development/demo mode
"""
import os
import json
import hashlib
import requests
import subprocess
from typing import Optional
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GCP_PROJECT = os.environ.get("GCP_PROJECT", "maroon-clean-up")
GCP_REGION = os.environ.get("GCP_REGION", "us-central1")
CLAUDE_LOCATION = os.environ.get("CLAUDE_LOCATION", "global")


# ---------------------------------------------------------------------------
# Access Token Helper
# ---------------------------------------------------------------------------

def get_access_token() -> Optional[str]:
    """Get GCP access token via gcloud CLI."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-access-token"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


# ---------------------------------------------------------------------------
# Gemini 1.5 Pro (Primary — Codex §3.1)
# ---------------------------------------------------------------------------

def call_gemini(prompt: str, max_tokens: int = 2048) -> Optional[str]:
    """
    Call Gemini 1.5 Pro via Vertex AI native SDK.
    Falls back gracefully if model/quota unavailable.
    """
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        vertexai.init(project=GCP_PROJECT, location=GCP_REGION)
        model = GenerativeModel("gemini-1.5-pro-preview-0409")
        response = model.generate_content(prompt)
        return response.text
    except ImportError:
        print("[AI] vertexai SDK not installed. Skipping Gemini.")
        return None
    except Exception as e:
        print(f"[AI] Gemini call failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Claude Opus 4.8 (Secondary — Codex §3.1)
# ---------------------------------------------------------------------------

def call_claude(prompt: str, max_tokens: int = 1024, stream: bool = False) -> Optional[str]:
    """
    Call Claude Opus 4.8 via Vertex AI Anthropic integration.
    Uses the global endpoint as per Anthropic's Vertex AI setup.
    """
    token = get_access_token()
    if not token:
        print("[AI] No GCP access token available. Skipping Claude.")
        return None

    url = (
        f"https://aiplatform.googleapis.com/v1/"
        f"projects/{GCP_PROJECT}/locations/{CLAUDE_LOCATION}/"
        f"publishers/anthropic/models/claude-opus-4-8:rawPredict"
    )

    payload = {
        "anthropic_version": "vertex-2023-10-16",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "stream": stream,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        if response.status_code == 200:
            data = response.json()
            # Anthropic response format
            if "content" in data and len(data["content"]) > 0:
                return data["content"][0].get("text", "")
            return json.dumps(data)
        else:
            print(f"[AI] Claude returned {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"[AI] Claude call failed: {e}")
        return None


# ---------------------------------------------------------------------------
# Unified AI Interface (Smart Fallback Chain)
# ---------------------------------------------------------------------------

def council_ai_call(prompt: str, max_tokens: int = 2048) -> str:
    """
    Unified AI call that implements the Codex §3.1 model priority:
    1. Gemini 1.5 Pro (primary)
    2. Claude Opus 4.8 (secondary)
    3. Mock response (development/demo)
    """
    # Try Gemini first
    print("[AI] Attempting Gemini 1.5 Pro...")
    result = call_gemini(prompt, max_tokens)
    if result:
        print("[AI] ✓ Gemini 1.5 Pro response received.")
        return result

    # Try Claude
    print("[AI] Gemini unavailable. Attempting Claude Opus 4.8...")
    result = call_claude(prompt, max_tokens)
    if result:
        print("[AI] ✓ Claude Opus 4.8 response received.")
        return result

    # Mock fallback
    print("[AI] All models unavailable. Using mock response for development.")
    mock_hash = hashlib.sha256(prompt[:100].encode()).hexdigest()[:16]
    return (
        f"[MOCK AI RESPONSE — {datetime.now(timezone.utc).isoformat()}]\n"
        f"The Maroon Council Core has processed the directive.\n"
        f"Analysis hash: {mock_hash}\n"
        f"All codex directives are validated. Proceed with execution.\n"
        f"Note: Connect Gemini or Claude via GCP Model Garden for live AI responses."
    )


# ---------------------------------------------------------------------------
# Codex Analysis Function
# ---------------------------------------------------------------------------

def analyze_ecosystem(codex_content: str) -> str:
    """Analyze the master codex using the AI model chain."""
    prompt = (
        "You are the Maroon Council Core — a sovereign AI orchestrator.\n"
        "Analyze the provided codex logic and enforce the architecture directives.\n"
        "Identify any gaps, misalignments, or opportunities for optimization.\n\n"
        f"MASTER CODEX:\n\n{codex_content}\n\n"
        "Execute Phase 1 Analysis. Be thorough and actionable."
    )
    return council_ai_call(prompt, max_tokens=4096)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("MAROON COUNCIL CORE — AI Integration Test")
    print("=" * 60)

    # Load the master codex
    codex_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), "..", "..", "MAROON_MASTER_CODEX.md"
    ))

    try:
        with open(codex_path, "r", encoding="utf-8") as f:
            codex_content = f.read()
        print(f"[Test] Master Codex loaded ({len(codex_content)} bytes)")
    except FileNotFoundError:
        codex_content = "Test codex content — the system is operational."
        print(f"[Test] Codex not found at {codex_path}, using test content.")

    # Run the AI analysis
    print("[Test] Running AI analysis chain...")
    result = analyze_ecosystem(codex_content)

    print("\n" + "=" * 60)
    print("AI ANALYSIS RESULT:")
    print("=" * 60)
    print(result)
