$ErrorActionPreference = "Continue"
$root = "C:\Users\maroon\.gemini\antigravity-ide\scratch\Maroon-Ecosystem-Root"

$pythonApps = @(
    "maroon-law-finance-core",
    "maroon-market-logistics",
    "maroon-pac-core",
    "maroon-palantir-lake",
    "maroon-council-core",
    "maroon-compliance-core"
)

$nodeApps = @(
    "maroon-market-core",
    "onitas-market-core",
    "maroon-real-estate-core"
)

# First create the venv globally in council core if it doesn't exist
$venvDir = Join-Path $root "maroon-council-core\venv"
if (-not (Test-Path $venvDir)) {
    Write-Host "Creating global venv in council core..."
    python -m venv $venvDir
}

$pipExe = Join-Path $venvDir "Scripts\pip.exe"

foreach ($app in $pythonApps) {
    $reqFile = Join-Path $root "$app\configs\requirements.txt"
    if (Test-Path $reqFile) {
        Write-Host "Installing pip requirements for $app..."
        & $pipExe install --no-cache-dir -r $reqFile
    } else {
        $reqFile2 = Join-Path $root "$app\requirements.txt"
        if (Test-Path $reqFile2) {
            & $pipExe install --no-cache-dir -r $reqFile2
        }
    }
}

foreach ($app in $nodeApps) {
    $appDir = Join-Path $root $app
    $pkgConfig = Join-Path $appDir "configs\package.json"
    $pkgLocal = Join-Path $appDir "package.json"
    
    if (Test-Path $pkgConfig) {
        Copy-Item $pkgConfig $pkgLocal -Force
    }
    
    if (Test-Path $pkgLocal) {
        Write-Host "Installing npm packages for $app..."
        Set-Location $appDir
        npm install
    }
}

Write-Host "All dependencies installed."
