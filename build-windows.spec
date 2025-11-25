# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Windows build
Watermark Tool v1.0.0
Targets: Windows 10+ (64-bit)
"""

import sys
import os

block_cipher = None

# Analysis: Find all dependencies
a = Analysis(
    ['watermark_tool.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('LICENSE.txt', '.'),
        ('README.txt', '.'),
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'PIL._imaging',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Pack collected files
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WatermarkTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86_64',  # 64-bit Windows (works on all modern Windows)
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
    version='version_info.txt' if os.path.exists('version_info.txt') else None,
)

# Note: Console=True shows terminal window during execution
# This is intentional for v1.0 - shows progress and errors
# Set to False in future versions for GUI-only mode
