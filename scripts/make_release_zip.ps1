# Build a portable source ZIP with the same tree as the repo, excluding local / generated bulk.
# Default output: sibling of this repo folder, named "<folder>-source-<timestamp>.zip"
# Run from anywhere:  pwsh -File scripts/make_release_zip.ps1
#
# Requires: tar.exe on PATH (Windows 10+ includes bsdtar; Git for Windows also provides tar).

param(
    [string]$OutZip = "",
    [switch]$SkipClean
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if (-not $SkipClean) {
    & (Join-Path $PSScriptRoot "clean_repo.ps1")
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$repoFolderName = Split-Path -Leaf $root
if (-not $OutZip) {
    $parent = Split-Path -Parent $root
    $OutZip = Join-Path $parent "${repoFolderName}-source-${stamp}.zip"
} else {
    $OutZip = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutZip)
}

if (-not (Get-Command tar -ErrorAction SilentlyContinue)) {
    Write-Error "tar.exe not found on PATH. Use Windows 10+ or install Git for Windows (includes tar)."
}

$excludes = @(
    ".venv", "venv", "env",
    ".git",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "build", "dist", ".eggs",
    ".coverage", "coverage.xml", "htmlcov",
    "__pycache__",
    "*.egg-info"
)

$tarArgs = @("-acf", $OutZip)
foreach ($pattern in $excludes) {
    $tarArgs += "--exclude=$pattern"
}
$tarArgs += "-C"
$tarArgs += $root
$tarArgs += "."

& tar @tarArgs

& (Join-Path $PSScriptRoot "verify_release_zip.ps1") -ZipPath $OutZip

Write-Host "Release ZIP written to: $OutZip"
Write-Host "Recipients should: unzip, then pip install -e `".[dev]`" (see README)."
