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
    pathex=[os.path.abspath('src')],
    binaries=[],
    datas=[item for item in [
        ('assets/logo.png', 'assets') if os.path.exists('assets/logo.png') else None,
        ('templates', 'templates') if os.path.exists('templates') else None
    ] if item is not None],
    hiddenimports=[
        'xlsxwriter',
        'xlsxwriter.workbook',
        'xlsxwriter.worksheet',
        'xlsxwriter.format',
        'xlsxwriter.utility',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.utils',
        'pandas',
        'pandas.io.excel._xlsxwriter',
        'numpy',
        'numpy.core',
        'numpy.core.multiarray',
        'pandas._libs',
        'pandas._libs.tslibs',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.skiplist',
        'tkinterdnd2',
        # Reconciliation modules
        'bank_ledger_processor',
        'sib_qr_processor',
        'demand_report_processor',
        'group_payment_processor',
        'phase3_processor',
        'merge_operations',
        'process_utils',
        # Processors subpackage
        'processors.bank_ledger_processor',
        'processors.sib_qr_processor',
        'processors.demand_report_processor',
        'processors.group_payment_processor',
        'processors.phase3_processor',
        'processors.merge_operations',
        'processors.process_utils',
        # Reconciliation subpackages
        'reconciliation.processors.bank_ledger_processor',
        'reconciliation.processors.sib_qr_processor',
        'reconciliation.processors.demand_report_processor',
        'reconciliation.processors.group_payment_processor',
        'reconciliation.processors.phase3_processor',
        'reconciliation.processors.merge_operations',
        'reconciliation.processors.process_utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch',
        'torchvision',
        'tensorflow',
        'tensorboard',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'cv2',
        'PIL.ImageQt',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BankReconciliationTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,  # Application icon
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BankReconciliationTool',
)
