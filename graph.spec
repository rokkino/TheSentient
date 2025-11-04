# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['graph.py'],
    pathex=['.'],  # Assicura che PyInstaller guardi nella cartella corrente
    binaries=[],
    datas=[
        ('rsi.py', '.'),          # Include il tuo add-on RSI
        ('spinner.gif', '.'),     # Include il file GIF
        ('icona.ico', '.')        # Include l'icona per setWindowIcon
    ],
    hiddenimports=[
        'PyQt6.sip',
        'PyQt6.QtGui',
        'PyQt6.QtCore',
        'PyQt6.QtWidgets',
        'matplotlib.backends.backend_qtagg' # Backend Matplotlib per PyQt
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
    name='PortfolioTracker', # Il nome del tuo file .exe
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # <-- IMPORTANTE: Nasconde la console (modalità finestra)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'       # <-- IMPORTANTE: Usa il file .ico per l'eseguibile
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PortfolioTracker' # Il nome della cartella di output
)