# -*- mode: python ; coding: utf-8 -*-

import os
import matplotlib

# --- INIZIO Blocco per dati aggiuntivi ---
# Trova il percorso dei dati di Matplotlib (necessari per mplfinance)
mpl_data_path = matplotlib.get_data_path()

# Elenca tutti i file che il tuo script deve trovare
# (percorso_sorgente, cartella_destinazione_nel_bundle)
added_files = [
    ('icon.ico', '.'),     # icon.ico is correct
    ('spinner.gif', '.'),   
    (mpl_data_path, 'mpl-data') 
]

# Elenca gli import che PyInstaller potrebbe non trovare
hidden_imports = [
    'pandas._libs.tslibs',
    'yfinance',
    'transformers',
    'torch',
    'beautifulsoup4',
    'PyQt6.sip' # Aggiunto per sicurezza con PyQt6
    'accelerate'
]
# --- FINE Blocco per dati aggiuntivi ---


a = Analysis(
    ['graph.py'],  # Il tuo script Python principale
    pathex=[],
    binaries=[],
    datas=added_files,       
    hiddenimports=hidden_imports, 
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
    exclude_binaries=True,
    name='TheSentient',       
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,            # Impostato a False per nascondere la console (è una GUI)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icona.ico'          
)