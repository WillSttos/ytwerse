# -*- mode: python ; coding: utf-8 -*-
"""
YTWERSE — PyInstaller Spec File
Generates a single standalone YTWERSE.exe.

Usage:
    pyinstaller ytwerse.spec

Output: dist/YTWERSE.exe
"""

import sys
import os

block_cipher = None

# Collect all files from _app/ to bundle inside the exe
_app_datas = []

# Templates
for root, dirs, files in os.walk('_app/templates'):
    for f in files:
        src = os.path.join(root, f)
        dst = os.path.join('_app', 'templates')
        _app_datas.append((src, dst))

# Static files
for root, dirs, files in os.walk('_app/static'):
    for f in files:
        src = os.path.join(root, f)
        dst = os.path.join('_app', 'static')
        _app_datas.append((src, dst))

# Python source files in _app/
for f in os.listdir('_app'):
    if f.endswith('.py') or f.endswith('.txt'):
        _app_datas.append((os.path.join('_app', f), '_app'))

# Icon asset
_app_datas.append(('assets/ytwerse-logo-icon.ico', 'assets'))

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=_app_datas,
    hiddenimports=[
        # Flask ecosystem
        'flask',
        'flask.templating',
        'flask.json',
        'jinja2',
        'jinja2.ext',
        'werkzeug',
        'werkzeug.serving',
        'werkzeug.routing',
        # Waitress WSGI server
        'waitress',
        'waitress.server',
        'waitress.runner',
        'waitress.utilities',
        'waitress.task',
        'waitress.channel',
        # HTTP requests
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        # PyWebView
        'webview',
        'webview.platforms.winforms',
        'clr',
        # Subprocess / OS
        'subprocess',
        're',
        'json',
        'queue',
        'threading',
        'zipfile',
        'shutil',
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
    a.binaries,
    a.datas,
    [],
    name='YTWERSE',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No black terminal window
    icon='assets/ytwerse-logo-icon.ico', # App icon
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
