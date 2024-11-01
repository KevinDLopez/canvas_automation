# -*- mode: python ; coding: utf-8 -*-

# Import required modules
from PyInstaller.utils.hooks import collect_data_files
import matplotlib

# Collect the Matplotlib data files
matplotlib_datas = collect_data_files('matplotlib')

# Define your application data files
app_datas = [
    ('client_secrets.json', 'client_secrets.json'),
    ('assets', 'assets'),
]

# Combine all data files
datas = matplotlib_datas + app_datas

a = Analysis(
    ['GradingAutomationUI.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['matplotlib_font_cache.py'],
    excludes=[],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GradingAutomation',
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
    icon=['assets/app_icon.png'],
)

app = BUNDLE(
    exe,
    name='GradingAutomation.app',
    icon='assets/app_icon.png',
    bundle_identifier=None,
)
