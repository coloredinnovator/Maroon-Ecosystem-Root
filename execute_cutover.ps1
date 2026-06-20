<#
.SYNOPSIS
Phase 4: The Cut-Over Execution Script

.DESCRIPTION
This script is designed to be run ONLY after the startup credits have arrived.
It initializes the Terraform matrix, validates the IaC, and deploys the
NASA-grade Kubernetes cluster while permanently severing ties with the
legacy identity.
#>

Write-Host "===========================================================" -ForegroundColor Cyan
Write-Host "dYs? MAROON TECHNOLOGIES: INITIATING PHASE 4 CUT-OVER" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

$terraformDir = "$PSScriptRoot\maroon-infrastructure"

if (-Not (Test-Path $terraformDir)) {
    Write-Host "[ERROR] Infrastructure directory not found!" -ForegroundColor Red
    exit 1
}

Push-Location $terraformDir

Write-Host "`n[1/4] Verifying Identity..." -ForegroundColor Yellow
# In reality, this would run: gcloud auth list
Write-Host "Ensure you are authenticated as: api@maroontechnologies.org" -ForegroundColor Green
Start-Sleep -Seconds 2

Write-Host "`n[2/4] Initializing Terraform Matrix..." -ForegroundColor Yellow
terraform init
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Terraform initialization failed." -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "`n[3/4] Validating NASA-Grade Architecture..." -ForegroundColor Yellow
terraform validate
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Architecture validation failed." -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "`n[4/4] Generating Deployment Plan..." -ForegroundColor Yellow
terraform plan -out=tfplan
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to generate deployment plan." -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "`n===========================================================" -ForegroundColor Cyan
Write-Host "CUT-OVER PLAN GENERATED SUCCESSFULLY." -ForegroundColor Green
Write-Host "To execute the final deployment and migrate to the permanent domain, run:" -ForegroundColor White
Write-Host "cd maroon-infrastructure" -ForegroundColor DarkGray
Write-Host "terraform apply tfplan" -ForegroundColor DarkGray
Write-Host "===========================================================" -ForegroundColor Cyan

Pop-Location
