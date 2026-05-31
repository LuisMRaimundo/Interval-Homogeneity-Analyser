# Remove generated / local artefacts before zipping or committing (PowerShell).
# Run from repo root:  pwsh -File scripts/clean_repo.ps1
# Optional: also remove local virtualenvs (destructive):  pwsh -File scripts/clean_repo.ps1 -IncludeVenv

param(
    [switch]$IncludeVenv
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" -Force | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force
}
foreach ($d in @(".pytest_cache", ".mypy_cache", ".ruff_cache", "build", "dist", ".eggs")) {
    if (Test-Path $d) {
        Remove-Item -LiteralPath $d -Recurse -Force
    }
}
Get-ChildItem -Path . -Recurse -Directory -Filter "*.egg-info" -Force | ForEach-Object {
    Remove-Item -LiteralPath $_.FullName -Recurse -Force
}
Get-ChildItem -Path . -Recurse -File -Include "*.docx", "*.mhtml" -Force -ErrorAction SilentlyContinue | Remove-Item -Force
foreach ($f in @(".coverage", "coverage.xml")) {
    if (Test-Path $f) {
        Remove-Item -LiteralPath $f -Force
    }
}
if (Test-Path "htmlcov") {
    Remove-Item -LiteralPath "htmlcov" -Recurse -Force
}
foreach ($d in @("results", "results_ci", "results_batch")) {
    if (Test-Path $d) {
        Remove-Item -LiteralPath $d -Recurse -Force
    }
}
$reportsDir = Join-Path $root "docs\reports"
if (Test-Path $reportsDir) {
    Get-ChildItem -Path $reportsDir -Recurse -File -Include "*.csv", "*.json", "*.md" |
        Where-Object { $_.Name -ne "README.md" } |
        Remove-Item -Force
    $tmp = Join-Path $reportsDir "_tmp"
    if (Test-Path $tmp) {
        Remove-Item -LiteralPath $tmp -Recurse -Force
    }
}

if ($IncludeVenv) {
    foreach ($d in @(".venv", "venv", "env")) {
        if (Test-Path $d) {
            Remove-Item -LiteralPath $d -Recurse -Force
        }
    }
    Write-Host "Also removed local virtualenv dirs (.venv / venv / env) if present."
}

Write-Host "Cleaned caches, build/dist/eggs, *.egg-info, *.docx, *.mhtml under $root"
if (-not $IncludeVenv) {
    Write-Host "Tip: pass -IncludeVenv to remove .venv / venv / env (you will need to recreate the env)."
}
