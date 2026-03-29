# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Murmur.app"""

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('data/dictionary.json', 'data'),
    ],
    hiddenimports=[
        'pynput.keyboard._darwin',
        'pynput._util.darwin',
        'AppKit',
        'Quartz',
        'Foundation',
        'objc',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'sounddevice',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='Murmur',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # No terminal window
    target_arch=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='Murmur',
)

app = BUNDLE(
    coll,
    name='Murmur.app',
    icon='Murmur.icns',
    bundle_identifier='com.murmur.dictation',
    info_plist={
        'CFBundleName': 'Murmur',
        'CFBundleDisplayName': 'Murmur',
        'CFBundleShortVersionString': '0.1.0',
        'LSMinimumSystemVersion': '13.0',
        'LSBackgroundOnly': False,
        'LSUIElement': True,  # Menu bar app — no dock icon
        'NSMicrophoneUsageDescription': 'Murmur needs microphone access for voice dictation.',
        'NSAppleEventsUsageDescription': 'Murmur needs accessibility access to inject text into applications.',
    },
)
