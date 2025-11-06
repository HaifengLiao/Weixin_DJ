# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['New_modeltest.py'],
    pathex=[],
    binaries=[],
    datas=[('checked_urls.txt', '.'), ('last.pt', '.'), ('yolov5', 'yolov5'), ('auto_login.js', '.')],
    hiddenimports=['mss', 'pyperclip', 'torch', 'cv2'],
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
    name='POTApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['iphone.png'],
)
