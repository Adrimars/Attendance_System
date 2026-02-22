# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Attendance System.

Build command (run from project root):
    pyinstaller attendance.spec

Output: dist\AttendanceSystem\AttendanceSystem.exe
"""

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        # Bundle the entire customtkinter theme/asset folder so the UI renders correctly
        (
            '.venv/Lib/site-packages/customtkinter',
            'customtkinter'
        ),
    ],
    hiddenimports=[
        'customtkinter',
        'gspread',
        'google.oauth2.service_account',
        'google.auth.transport.requests',
        'google.auth._default',
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
    name='AttendanceSystem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No black CMD window behind the GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AttendanceSystem',
)
