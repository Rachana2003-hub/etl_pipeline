# PowerShell script to simulate CI/CD checks locally (Linting & Unit Tests)
$ErrorActionPreference = "Stop"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "     Running Local CI/CD Simulation Checklist     " -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Python detected: $pythonVersion" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH." -ForegroundColor Red
    Exit 1
}

# 2. Check virtual environment
if ($null -eq $env:VIRTUAL_ENV) {
    Write-Host "[WARN] Not running in a Python virtual environment." -ForegroundColor Yellow
} else {
    Write-Host "[INFO] Active Virtual Environment: $env:VIRTUAL_ENV" -ForegroundColor Green
}

# 3. Install/upgrade developer and runtime requirements
Write-Host "`n[1/3] Installing dependencies..." -ForegroundColor Blue
try {
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    Write-Host "[PASS] Dependencies installed successfully." -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to install dependencies." -ForegroundColor Red
    Exit 1
}

# 4. Linting and formatting checks
Write-Host "`n[2/3] Running code linting & formatting checks (Ruff)..." -ForegroundColor Blue
$lintFailed = $false

Write-Host "-> Checking code formatting..." -ForegroundColor Gray
& ruff format --check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Code formatting issues found. Run 'ruff format .' to automatically fix." -ForegroundColor Yellow
    $lintFailed = $true
} else {
    Write-Host "[PASS] Code formatting checks passed." -ForegroundColor Green
}

Write-Host "-> Checking code quality and syntax..." -ForegroundColor Gray
& ruff check .
if ($LASTEXITCODE -ne 0) {
    Write-Host "[FAIL] Lint errors found. Run 'ruff check --fix .' to attempt automatic fixes." -ForegroundColor Yellow
    $lintFailed = $true
} else {
    Write-Host "[PASS] Code quality checks passed." -ForegroundColor Green
}

if ($lintFailed) {
    Write-Host "`n[ERROR] Linting checks failed. CI pipeline will fail on these steps." -ForegroundColor Red
    Exit 1
}

# 5. Run Unit Tests with coverage
Write-Host "`n[3/3] Running unit tests with pytest & coverage..." -ForegroundColor Blue
& python -m pytest --cov=. --cov-report=term-missing tests/
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n[ERROR] Some unit tests failed. CI pipeline will fail on this step." -ForegroundColor Red
    Exit 1
} else {
    Write-Host "`n[PASS] All unit tests completed successfully." -ForegroundColor Green
}

Write-Host "`n==================================================" -ForegroundColor Green
Write-Host "      Local CI Simulation Completed: SUCCESS!      " -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
