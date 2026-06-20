$ErrorActionPreference = "Continue"
$root = "C:\Users\maroon\.gemini\antigravity-ide\scratch\Maroon-Ecosystem-Root"
$pythonExe = Join-Path $root "maroon-council-core\venv\Scripts\python.exe"

$pythonServices = @(
    @{name="maroon-council-core"; port=8000; module="src.main:app"},
    @{name="maroon-palantir-lake"; port=8001; module="src.main:app"},
    @{name="maroon-law-finance-core"; port=8008; module="src.api:app"},
    @{name="maroon-market-logistics"; port=8009; module="src.router:app"},
    @{name="maroon-pac-core"; port=8010; module="src.api:app"}
)

foreach ($svc in $pythonServices) {
    $svcName = $svc.name
    $port = $svc.port
    $module = $svc.module
    $svcDir = Join-Path $root $svcName
    
    Write-Host "Booting $svcName on port $port..."
    # Run in background via Start-Process
    Start-Process -FilePath $pythonExe -ArgumentList "-m", "uvicorn", $module, "--host", "0.0.0.0", "--port", "$port" -WorkingDirectory $svcDir -WindowStyle Hidden
}

$nodeServices = @(
    @{name="maroon-market-core"; port=9000; cmd="start"},
    @{name="onitas-market-core"; port=3000; cmd="start"},
    @{name="maroon-real-estate-core"; port=4001; cmd="start"}
)

foreach ($svc in $nodeServices) {
    $svcName = $svc.name
    $port = $svc.port
    $cmd = $svc.cmd
    $svcDir = Join-Path $root $svcName
    
    if (Test-Path $svcDir) {
        Write-Host "Booting $svcName on port $port..."
        # set PORT
        $env:PORT = $port
        Start-Process -FilePath "npm.cmd" -ArgumentList "run", $cmd -WorkingDirectory $svcDir -WindowStyle Hidden
    }
}

Write-Host "All available services booted in background."
