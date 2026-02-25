# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

block_cipher = None

# Get project root and version info
project_root = Path(SPECPATH)
version_module = project_root / 'version.py'
exec(open(version_module).read())

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),  # Include assets folder
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtSvg',
        'PyQt5.QtNetwork',
        'svgwrite',
        'openpyxl',
        'dateutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'pytest',
        'pytest_qt',
        'pytest_cov',
        'sphinx',
        'black',
        'flake8',
        'mypy',
        'tests',
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
    name='CompactGantt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/favicon.ico',  # Application icon
    version_info={
        'version': __version__,
        'description': 'A PyQt5-based tool for creating compact Gantt charts',
        'product_name': APP_NAME,
        'company_name': APP_AUTHOR,
        'copyright': APP_COPYRIGHT,
        'file_version': __version__,
        'product_version': __version__,
    },
)
