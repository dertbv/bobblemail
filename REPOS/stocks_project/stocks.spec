# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# Get the current directory
app_dir = Path(os.getcwd())

# Define data files to include
datas = [
    # Templates directory
    (str(app_dir / 'templates'), 'templates'),
    # Static files
    (str(app_dir / 'static'), 'static'),
    # Documentation
    (str(app_dir / 'docs'), 'docs'),
    # Sample outputs (for reference)
    (str(app_dir / 'outputs'), 'outputs'),
]

# Hidden imports - modules that PyInstaller might miss
hiddenimports = [
    'pandas',
    'numpy',
    'yfinance',
    'requests',
    'matplotlib',
    'seaborn',
    'beautifulsoup4',
    'lxml',
    'flask',
    'werkzeug',
    'jinja2',
    'markupsafe',
    'itsdangerous',
    'click',
    'concurrent.futures',
    'threading',
    'queue',
    'dataclasses',
    'enum',
    'typing',
    'json',
    'csv',
    'sqlite3',
    'urllib3',
    'certifi',
    'charset_normalizer',
    'idna',
    'urllib',
    'http',
    'html',
    'xml',
    'email',
    'datetime',
    'decimal',
    'fractions',
    'math',
    'statistics',
    'time',
    'calendar',
    'locale',
    're',
    'unicodedata',
    'functools',
    'operator',
    'collections',
]

# Exclude unnecessary modules to reduce size
excludes = [
    'tkinter',
    'turtle',
    'test',
    'unittest',
    'pydoc',
    'doctest',
    'argparse',
    'jupyter',
    'notebook',
    'IPython',
    'qtconsole',
    'spyder',
    'pylint',
    'rope',
    'mypy',
    'flake8',
]

# Binary excludes
binaries = []

# Analysis
a = Analysis(
    ['stocks_launcher.py'],
    pathex=[str(app_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='stocks_launcher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Don't show console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Create app bundle
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='stocks_launcher'
)

# Create macOS app bundle
app = BUNDLE(
    coll,
    name='StocksAnalyzer.app',
    icon='assets/icon.icns',  # Will be created
    bundle_identifier='com.stocksanalyzer.app',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'Stocks Analyzer',
        'CFBundleDisplayName': 'Stocks Analyzer',
        'CFBundleExecutable': 'stocks_launcher',
        'CFBundleIdentifier': 'com.stocksanalyzer.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'STKA',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSBackgroundOnly': False,
        'LSUIElement': False,
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [],
        'NSPrincipalClass': 'NSApplication',
        'NSHumanReadableCopyright': 'Copyright © 2025 Stocks Analyzer',
        'CFBundleGetInfoString': 'Stocks Analyzer - Professional Stock Analysis Tool',
        'LSMinimumSystemVersion': '10.13',
    }
)