# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for a one-folder, windowed Windows build.

Build on a Windows machine (PyInstaller cannot cross-compile from Linux)
with the same Python minor version used for development:

    pyinstaller InventorySystem.spec --clean --noconfirm

Only read-only assets belong in ``datas`` below (an icon, a stylesheet, a
bundled font, etc.). Nothing mutable is bundled: ``store.db``, ``images/``,
``logs/``, and ``backups/`` are all created next to the executable on
first run by app/utils/paths.py, which detects `sys.frozen` and resolves
its writable base directory to the folder containing the .exe.
"""

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis

block_cipher = None

# Add (source_path, dest_dir_in_bundle) tuples here for any read-only asset,
# e.g. ("assets/icon.ico", ".") for a window/taskbar icon referenced from
# app/ui/main_window.py.
DATAS = []

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=DATAS,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InventorySystem",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # windowed: no console window behind the GUI
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # set to an .ico path once branding assets exist
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="InventorySystem",
)
