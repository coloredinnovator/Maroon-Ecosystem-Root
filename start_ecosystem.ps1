$ErrorActionPreference = "Stop"
$root = "C:\Users\maroon\.gemini\antigravity-ide\scratch\Maroon-Ecosystem-Root"

$services = @(
    @{name="maroon-council-core"; port=8000},
    @{name="maroon-compliance-core"; port=8002},
    @{name="maroon-market-logistics"; port=8004},
    @{name="maroon-medical-opco"; port=8005},
    @{name="maroon-medical-diagnostics"; port=8006},
    @{name="maroon-medical-rehab"; port=8007},
    @{name="maroon-pac-core"; port=8008},
    @{name="maroon-law-finance-core"; port=8009},
    @{name="maroon-palantir-lake"; port=8010}
)

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "🚀 IGNITING MAROON SOVEREIGN ECOSYSTEM" -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan

foreach ($svc in $services) {
    $svcName = $svc.name
    $port = $svc.port
    $svcDir = Join-Path $root $svcName
    $pythonExe = Join-Path $svcDir "venv\Scripts\python.exe"
    $srcDir = Join-Path $svcDir "src"
    
    if (-not (Test-Path $pythonExe)) {
        Write-Host "WARNING: Virtual environment not found for $svcName. Skipping." -ForegroundColor Yellow
        continue
    }

    Write-Host "Starting $svcName on port $port..." -ForegroundColor White
    
    # Start the process in a new window so it stays alive and the user can see the logs
    $args = "-m uvicorn main:app --host 0.0.0.0 --port $port --app-dir ""$srcDir"""
    Start-Process -FilePath $pythonExe -ArgumentList $args -WorkingDirectory $svcDir -WindowStyle Normal
    
    Start-Sleep -Seconds 1
}

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "✅ All Python services have been launched in separate windows." -ForegroundColor Green
Write-Host "To monitor status, you can check the individual console windows." -ForegroundColor Green
Write-Host "===========================================================" -ForegroundColor Cyan
