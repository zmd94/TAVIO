# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller --onedir build specification for TAVIO on Windows 10/11 (64-bit)."""

from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

PROJECT_ROOT = Path(SPECPATH).resolve().parent
SRC_ROOT = PROJECT_ROOT / "src"
RESOURCES_DIR = PROJECT_ROOT / "resources"
ICON_PATH = RESOURCES_DIR / "icons" / "tavio.ico"

ortools_datas, ortools_binaries, ortools_hiddenimports = collect_all("ortools")
reportlab_datas, reportlab_binaries, reportlab_hiddenimports = collect_all("reportlab")
openpyxl_hiddenimports = collect_submodules("openpyxl")

datas = [
    (str(RESOURCES_DIR), "resources"),
    *ortools_datas,
    *reportlab_datas,
]

binaries = [
    *ortools_binaries,
    *reportlab_binaries,
]

hiddenimports = [
    *ortools_hiddenimports,
    *reportlab_hiddenimports,
    *openpyxl_hiddenimports,
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
    excludes=["tkinter", "unittest", "pytest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
    icon=str(ICON_PATH) if ICON_PATH.is_file() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TAVIO",
)
