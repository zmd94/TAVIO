<#
.SYNOPSIS
    Builds the TAVIO Windows desktop distribution using PyInstaller (--onedir).
#>
[CmdletBinding()]
param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot

try {
    Write-Host "=== TAVIO Phase 0 Windows Build ===" -ForegroundColor Cyan

    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "Python executable not found in PATH. Activate your .venv first."
    }

    if (-not $SkipTests) {
        Write-Host "Running pytest..." -ForegroundColor Yellow
        python -m pytest
        if ($LASTEXITCODE -ne 0) {
            throw "pytest failed. Aborting build."
        }

        Write-Host "Running ruff check..." -ForegroundColor Yellow
        python -m ruff check src tests
        if ($LASTEXITCODE -ne 0) {
            throw "ruff check failed. Aborting build."
        }
    }

    foreach ($dir in @("build", "dist")) {
        if (Test-Path $dir) {
            Write-Host "Cleaning $dir..." -ForegroundColor DarkGray
            Remove-Item -Recurse -Force $dir
        }
    }

    Write-Host "Running PyInstaller (--onedir)..." -ForegroundColor Yellow
    python -m PyInstaller --noconfirm --clean packaging\tavio.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed."
    }

    $ExePath = Join-Path $ProjectRoot "dist\TAVIO\TAVIO.exe"
    if (-not (Test-Path $ExePath)) {
        throw "Expected executable was not generated at $ExePath"
    }

    Write-Host "Build succeeded: $ExePath" -ForegroundColor Green
}
finally {
    Pop-Location
}
