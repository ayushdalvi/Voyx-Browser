# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py', 'browser_window.py', 'ai_panel.py', 'userscript_manager.py', 'security_manager.py', 'paywall_bypass.py', 'security_settings.py'],
    pathex=[],
    binaries=[],
    datas=[('userscripts', 'userscripts')],
    hiddenimports=['PyQt5', 'PyQt5.QtWebEngineWidgets', 'PyQt5.QtCore', 'PyQt5.QtWidgets', 'PyQt5.QtWebEngine', 'requests'],
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
    name='VoyxBrowser',
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
)
