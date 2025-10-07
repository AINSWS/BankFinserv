# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src\\main.py'],
    pathex=['src', '.'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinterdnd2',
        'tkinterdnd2.tkdnd',
        'pandas',
        'openpyxl',
        'xlrd',
        'numpy',
        'datetime',
        'os',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        'ui_multi',
        'uploader'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'PIL',
        'PyQt5',
        'torch',
        'torchvision',
        'cv2',
        'scipy',
        'IPython',
        'jedi',
        'jupyter',
        'notebook',
        'zmq',
        'win32com',
        'pythoncom',
        'pywintypes'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
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
    icon=None
)