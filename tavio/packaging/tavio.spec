# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller --onedir build specification for TAVIO on Windows 10/11 (64-bit)."""

from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

PROJECT_ROOT = Path(SPECPATH).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
RESOURCES_DIR = PROJECT_ROOT / "resources"
ASSETS_DIR = PROJECT_ROOT / "packaging" / "assets"
ICON_PATH = ASSETS_DIR / "TAVIO.ico"

if not ASSETS_DIR.is_dir():
    raise FileNotFoundError(f"TAVIO branding assets directory not found: {ASSETS_DIR}")

required_assets = ("TAVIO.ico", "TAVIO_icon.png", "TAVIO_icon_vertical.png")
missing_assets = [name for name in required_assets if not (ASSETS_DIR / name).is_file()]
if missing_assets:
    raise FileNotFoundError(
        "Missing required TAVIO branding assets: " + ", ".join(missing_assets)
    )

ortools_datas, ortools_binaries, ortools_hiddenimports = collect_all("ortools")
reportlab_datas, reportlab_binaries, reportlab_hiddenimports = collect_all("reportlab")
openpyxl_datas, openpyxl_binaries, openpyxl_hiddenimports = collect_all("openpyxl")

datas = [
    (str(RESOURCES_DIR), "resources"),
    (str(ASSETS_DIR), "resources/assets"),
    *ortools_datas,
    *reportlab_datas,
    *openpyxl_datas,
]

binaries = [
    *ortools_binaries,
    *reportlab_binaries,
    *openpyxl_binaries,
]

hiddenimports = [
    *ortools_hiddenimports,
    *reportlab_hiddenimports,
    *openpyxl_hiddenimports,
    "et_xmlfile",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

a = Analysis(
    [str(SRC_ROOT / "tavio" / "main.py")],
    pathex=[str(SRC_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "_pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TAVIO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_PATH),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TAVIO",
)
