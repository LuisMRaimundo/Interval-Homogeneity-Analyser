# Fail if a release archive lists forbidden local/generated paths (venv, caches, egg-info, bytecode).
# Usage: pwsh -File scripts/verify_release_zip.ps1 -ZipPath "C:\path\to\archive.zip"
# Intended for ZIPs produced by make_release_zip.ps1 (tar/zip); also works on typical zip layouts.

param(
    [Parameter(Mandatory = $true)]
    [string]$ZipPath
)

$ErrorActionPreference = "Stop"
$ZipPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ZipPath)
if (-not (Test-Path -LiteralPath $ZipPath)) {
    Write-Error "ZIP not found: $ZipPath"
}

if (-not (Get-Command tar -ErrorAction SilentlyContinue)) {
    Write-Error "tar.exe not found on PATH (needed to list archive contents)."
}

# Match / or \ so listings from mixed zip tools still fail verification.
$pattern = '(^|[\\/])\.venv([\\/]|$)|(^|[\\/])venv([\\/]|$)|(^|[\\/])env([\\/]|$)|__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|\.egg-info([\\/]|$)'
$matches = @(& tar -tf $ZipPath | Select-String -Pattern $pattern -AllMatches)
if ($matches.Count -gt 0) {
    $sample = ($matches | Select-Object -First 40 | ForEach-Object { $_.Line }) -join "`n"
    Write-Error ("ZIP contains forbidden paths ({0} matches). First lines:`n{1}" -f $matches.Count, $sample)
}
Write-Host "ZIP verification OK: no venv, caches, egg-info, or __pycache__ paths in listing."
