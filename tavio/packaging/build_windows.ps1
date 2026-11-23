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
    Write-Host "=== TAVIO Windows Build ===" -ForegroundColor Cyan

    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        throw "Python executable not found in PATH. Activate your .venv first."
    }

    $AssetDir = Join-Path $PSScriptRoot "assets"
    foreach ($AssetName in @("TAVIO.ico", "TAVIO_icon.png", "TAVIO_icon_vertical.png")) {
        if (-not (Test-Path (Join-Path $AssetDir $AssetName))) {
            throw "Required branding asset is missing: $AssetName"
        }
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
    python -m PyInstaller --noconfirm --clean packaging\\tavio.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build failed."
    }

    $ExePath = Join-Path $ProjectRoot "dist\\TAVIO\\TAVIO.exe"
    if (-not (Test-Path $ExePath)) {
        throw "Expected executable was not generated at $ExePath"
    }

    $InternalQss = Join-Path $ProjectRoot "dist\\TAVIO\\_internal\\resources\\styles\\main.qss"
    $RootQss = Join-Path $ProjectRoot "dist\\TAVIO\\resources\\styles\\main.qss"
    if (-not ((Test-Path $InternalQss) -or (Test-Path $RootQss))) {
        throw "Bundled stylesheet resource (main.qss) was not found in dist\\TAVIO."
    }

    $BundledIcon = Join-Path $ProjectRoot "dist\\TAVIO\\_internal\\resources\\assets\\TAVIO_icon.png"
    $BundledLogo = Join-Path $ProjectRoot "dist\\TAVIO\\_internal\\resources\\assets\\TAVIO_icon_vertical.png"
    $RootBundledIcon = Join-Path $ProjectRoot "dist\\TAVIO\\resources\\assets\\TAVIO_icon.png"
    $RootBundledLogo = Join-Path $ProjectRoot "dist\\TAVIO\\resources\\assets\\TAVIO_icon_vertical.png"

    if (-not ((Test-Path $BundledIcon) -or (Test-Path $RootBundledIcon))) {
        throw "Bundled application icon (TAVIO_icon.png) was not found in dist\\TAVIO."
    }
    if (-not ((Test-Path $BundledLogo) -or (Test-Path $RootBundledLogo))) {
        throw "Bundled vertical logo (TAVIO_icon_vertical.png) was not found in dist\\TAVIO."
    }

    Write-Host "Build succeeded: $ExePath" -ForegroundColor Green
    Write-Host "Branding assets verified in the Windows distribution." -ForegroundColor Green
    Write-Host "Next step: launch '$ExePath' and verify the window, taskbar, and EXE icon." -ForegroundColor Cyan
}
finally {
    Pop-Location
}
