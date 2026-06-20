@echo off
echo ===========================================================
echo IGNITING MAROON SOVEREIGN ECOSYSTEM
echo ===========================================================

cd /d "%~dp0"

echo Starting Council Core (Port 8000)
start "Maroon Council Core" cmd /k "cd maroon-council-core & .\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --app-dir src"

echo Starting Compliance Core (Port 8002)
start "Maroon Compliance Core" cmd /k "cd maroon-compliance-core & .\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8002 --app-dir src"

echo Starting Market Logistics (Port 8004)
start "Maroon Market Logistics" cmd /k "cd maroon-market-logistics & .\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8004 --app-dir src"

echo Starting Medical OpCo (Port 8005)
start "Maroon Medical OpCo" cmd /k "cd maroon-medical-opco & .\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8005 --app-dir src"

echo Starting Medical Diagnostics (Port 8006)
start "Maroon Medical Diagnostics" cmd /k "cd maroon-medical-diagnostics & .\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8006 --app-dir src"

echo Starting Medical Rehab (Port 8007)
start "Maroon Medical Rehab" cmd /k "cd maroon-medical-rehab & .\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8007 --app-dir src"

echo Starting PAC Core (Port 8008)
start "Maroon PAC Core" cmd /k "cd maroon-pac-core & .\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8008 --app-dir src"

echo Starting Law and Finance Core (Port 8009)
start "Maroon Law and Finance Core" cmd /k "cd maroon-law-finance-core & .\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8009 --app-dir src"

echo Starting Palantir Lake (Port 8010)
start "Maroon Palantir Lake" cmd /k "cd maroon-palantir-lake & .\venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8010 --app-dir src"

echo ===========================================================
echo All Python services have been launched in separate windows.
echo ===========================================================
