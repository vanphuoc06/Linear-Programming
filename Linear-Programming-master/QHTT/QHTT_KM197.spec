# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for QHTT_KM197 (onedir mode - thư mục)

import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Thu thập tất cả submodule cần thiết
uvicorn_hidden  = collect_submodules('uvicorn')
anyio_hidden    = collect_submodules('anyio')
starlette_hidden = collect_submodules('starlette')
fastapi_hidden  = collect_submodules('fastapi')
webview_hidden  = collect_submodules('webview')
multipart_hidden = collect_submodules('multipart')
all_hidden = (
    uvicorn_hidden + anyio_hidden + starlette_hidden +
    fastapi_hidden + webview_hidden + multipart_hidden +
    [
        'fractions', 'numpy', 'numpy.core', 'numpy.lib',
        'email.mime', 'email.mime.text', 'email.mime.multipart',
        'logging.handlers', 'encodings',
        # WebView2 / pywebview Windows platform
        'webview.platforms.winforms',
        'webview.platforms.edgechromium',
        'webview.platforms.mshtml',
        'clr_loader',
        # asyncio / uvicorn loop
        'asyncio',
        'asyncio.windows_events',
        'asyncio.windows_utils',
    ]
)

a = Analysis(
    ['run_app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # Bundle thư mục gui/
        ('gui', 'gui'),
        # Cho phép load các DLL tải về từ internet (tránh block bởi Windows)
        ('QHTT_KM197.exe.config', '.'),
        # Bundle file bg.jpg từ thư mục chính vào root của exe
        # ('bg.jpg', '.'),
    ],
    hiddenimports=all_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',   
        'torch',     
        'torchvision',
        'cv2',       
        'easyocr',  
        'scipy',     
        'pandas',    
        'pyarrow',   
        'tensorboard',
        'skimage',
        'shapely',
        'fastparquet',
        'cramjam',
        'IPython',
        'jedi',
        'sqlite3',
        'matplotlib',
        'contourpy',
        'cycler',
        'kiwisolver',
        'fontTools',
        'pyparsing',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Trong chế độ onedir, EXE chỉ chứa scrip khởi động và các metadata cơ bản
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='QHTT_KM197',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,               
    console=False,           # Đặt thành False để ẨN console đen khi chạy
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

# COLLECT sẽ gom toàn bộ binaries, zipfiles, và datas vào một thư mục
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,               # Tắt UPX cho toàn bộ thư mục
    upx_exclude=[],
    name='QHTT_KM197',  # Tên thư mục đầu ra
)
