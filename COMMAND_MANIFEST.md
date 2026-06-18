# 🛠️ MAROON COMMAND MANIFEST

This document lists all active agent-executable commands for the Maroon Master Codex.

## 🏗️ Infrastructure Commands
- `powershell.exe -ExecutionPolicy Bypass -File scripts/instantiate_repos.ps1` : Creates all directories defined in REPO_MAP.yaml locally.
- `terraform apply -auto-approve` : Deploys the GCP/Azure/AWS infrastructure.
- `gh repo sync <repo>` : Synchronizes a specific repository with the master branch.

## 🧠 Agent Orchestration
- `python src/orchestrator.py --task "analyze_logs"` : Wakes the Maroon Council to process data.
- `python src/compliance.py --check` : Runs the Zero-Trust Gatekeeper checks.
