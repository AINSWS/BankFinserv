# -*- mode: python ; coding: utf-8 -*-

import os

# Check if logo exists
icon_path = 'assets/logo.ico'
if not os.path.exists(icon_path):
    icon_path = None
    print("⚠️ WARNING: Logo file not found at assets/logo.ico")
    print("   Application will use default icon.")
    print("   See assets/README.md for instructions on adding a logo.")

a = Analysis(
    ['src\\main_modular.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/logo.png', 'assets')] if os.path.exists('assets/logo.png') else [],
    hiddenimports=['xlsxwriter', 'openpyxl'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BankReconciliationTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,  # Application icon
)
