# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['New_modeltest.py'],  # 将上面的代码保存为这个文件名
    pathex=[],
    binaries=[],
    datas=[
        ('last.pt', '.'),  # 确保模型文件在正确位置
        ('auto_login.js', '.'),  # 确保JS文件在正确位置
    ],
    hiddenimports=['yolov5'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='smart_detector',
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
)
