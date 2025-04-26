# -*- mode: python ; coding: utf-8 -*-
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

"""
Run with:
  $ pyinstaller bin/tt-triage.spec
"""

import sys
import os

# Add the path to ttexalens module (git root of this file)
import subprocess

def get_git_root():
    try:
        git_root = subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], stderr=subprocess.STDOUT).strip()
        return git_root.decode('utf-8')
    except subprocess.CalledProcessError:
        return "."

ttexalens_path = get_git_root()
sys.path.insert(0, ttexalens_path)

# Path to so files
so_files = [
    os.path.join(ttexalens_path, f'build/lib/libdevice.so'),
    os.path.join(ttexalens_path, f'build/lib/ttexalens_pybind.so')
]

# Create binaries list for PyInstaller
binary_tuples = [(so_file, 'build/lib') for so_file in so_files]

block_cipher = None

a = Analysis(
    ['tt-triage.py'],
    pathex=['.', ttexalens_path],
    binaries=binary_tuples,
    datas=[],
    hiddenimports=['ttexalens', 'ttexalens.tt_exalens_init', 'ttexalens.tt_exalens_lib', 'ttexalens.coordinate'],
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
    name='tt-triage',
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
