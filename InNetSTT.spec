# -*- mode: python ; coding: utf-8 -*-
# ──────────────────────────────────────────────────────────────────────────────
# IN NET STT Convertor — PyInstaller Spec
# Produces a single-file Windows .exe with no console window.
#
# BUILD:
#   pip install pyinstaller
#   pyinstaller InNetSTT.spec
#
# OUTPUT: dist\InNetSTT.exe
# ──────────────────────────────────────────────────────────────────────────────

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    # Bundle the templates folder so Flask can find index.html at runtime
    datas=[
        ('templates', 'templates'),
    ],
    # edge-tts uses several submodules that PyInstaller misses on auto-scan
    hiddenimports=[
        'edge_tts',
        'edge_tts.communicate',
        'edge_tts.list_voices',
        'edge_tts.models',
        'edge_tts.submaker',
        'edge_tts.util',
        'aiohttp',
        'aiohttp.connector',
        'aiohttp.client',
        'aiohttp.streams',
        'asyncio',
        'flask',
        'flask.templating',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.debug',
        'click',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Strip heavy unused packages to keep exe size down
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'test',
        'unittest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
    optimize=1,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='InNetSTT',
    # Icon: PyInstaller expects a .ico file.
    # Run convert_icon.py first (see build.bat) to produce Assets\logo.ico
    icon='Assets\\logo.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # False = no black console window — app opens straight to browser
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows-only version info shown in Explorer "Details" tab
    version='file_version_info.txt',
)
