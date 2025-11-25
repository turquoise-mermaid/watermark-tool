# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Mac build
Watermark Tool v1.0.0
Targets: macOS 10.13+ (Intel x86_64)
Compatible with Apple Silicon via Rosetta 2
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
    [],
    exclude_binaries=True,
    name='WatermarkTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86_64',  # Intel Macs (works on Apple Silicon via Rosetta 2)
    codesign_identity=None,
    entitlements_file=None,
)

# Collect all files for the app bundle
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WatermarkTool',
)

# Create Mac application bundle (.app)
app = BUNDLE(
    coll,
    name='WatermarkTool.app',
    icon='icon.icns' if os.path.exists('icon.icns') else None,
    bundle_identifier='com.catasticcreations.watermarktool',
    version='1.0.0',
    info_plist={
        # Basic app info
        'CFBundleName': 'Watermark Tool',
        'CFBundleDisplayName': 'Watermark Tool',
        'CFBundleGetInfoString': 'Watermark Tool - Protect your designs',
        'CFBundleIdentifier': 'com.catasticcreations.watermarktool',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': '????',
        'CFBundleExecutable': 'WatermarkTool',
        
        # Copyright and category
        'NSHumanReadableCopyright': '© 2024 Turquoise Sunrise LLC',
        'LSApplicationCategoryType': 'public.app-category.graphics-design',
        
        # System requirements
        'LSMinimumSystemVersion': '10.13.0',  # macOS High Sierra and later
        'LSMinimumSystemVersionByArchitecture': {
            'x86_64': '10.13.0',
        },
        
        # Display settings
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        
        # Permissions (none needed for this app)
        'NSAppleEventsUsageDescription': 'This app does not use Apple Events',
    },
)

# Note: Console=True shows terminal window during execution
# This is intentional for v1.0 - shows progress and errors
# Set to False in future versions for GUI-only mode
