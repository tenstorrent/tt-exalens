#!/usr/bin/env bash
# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0
#
# Custom cibuildwheel `repair-wheel-command` for tt-exalens wheels.
#
# Problem: the SFPI-vendored `riscv-tt-elf-gdb` binary inside the wheel is
# built against debian's glibc/libstdc++. It needs GLIBCXX_3.4.30 (libstdc++
# from gcc-12+), which is newer than the manylinux_2_34 baseline ships
# (gcc-11.5, GLIBCXX_3.4.29 max). If we let auditwheel inspect the whole
# wheel, repair fails with "too-recent versioned symbols".
#
# Approach: pull the GDB binary out of the wheel, run auditwheel repair on
# the rest (so the native `_native_ttexalens.so` and its deps get the proper
# manylinux treatment), then re-insert GDB and repack. The wheel ends up
# tagged manylinux_2_34 despite the GDB binary needing a newer libstdc++ at
# runtime — users on systems with libstdc++ < gcc-12 (Ubuntu 22.04 stock,
# Debian 11) can install the wheel but cannot launch GDB. This matches what
# tt-exalens has always required in practice.
set -euo pipefail

WHEEL=$1
DEST_DIR=$2

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

# Path of the GDB binary relative to the unpacked wheel root.
GDB_REL="ttexalens/sfpi/compiler/bin/riscv-tt-elf-gdb"

# Pre-create every output dir we hand to `python -m wheel pack` / `auditwheel
# repair`. The wheel CLI doesn't create -d targets implicitly and fails with
# FileNotFoundError if the path is absent.
mkdir -p "$WORK/unpacked" "$WORK/stripped" "$WORK/repaired" "$WORK/final" "$DEST_DIR"

# 1. Unpack original wheel.
python -m wheel unpack -d "$WORK/unpacked" "$WHEEL"
PKG_DIR=$(find "$WORK/unpacked" -mindepth 1 -maxdepth 1 -type d)

# 2. Stash GDB if present (other archs may not include it).
if [ -f "$PKG_DIR/$GDB_REL" ]; then
    mkdir -p "$WORK/gdb_stash/$(dirname "$GDB_REL")"
    mv "$PKG_DIR/$GDB_REL" "$WORK/gdb_stash/$GDB_REL"
    echo "Stashed $GDB_REL outside the wheel for auditwheel."
fi

# 3. Repack without GDB and run auditwheel repair on the leaner wheel.
python -m wheel pack -d "$WORK/stripped" "$PKG_DIR"
STRIPPED_WHEEL=$(ls "$WORK/stripped"/*.whl)

auditwheel repair -w "$WORK/repaired" "$STRIPPED_WHEEL"
REPAIRED_WHEEL=$(ls "$WORK/repaired"/*.whl)

# 4. Unpack repaired wheel, restore GDB, repack to DEST_DIR.
python -m wheel unpack -d "$WORK/final" "$REPAIRED_WHEEL"
FINAL_DIR=$(find "$WORK/final" -mindepth 1 -maxdepth 1 -type d)

if [ -f "$WORK/gdb_stash/$GDB_REL" ]; then
    mkdir -p "$FINAL_DIR/$(dirname "$GDB_REL")"
    mv "$WORK/gdb_stash/$GDB_REL" "$FINAL_DIR/$GDB_REL"
    echo "Restored $GDB_REL into the repaired wheel."
fi

python -m wheel pack -d "$DEST_DIR" "$FINAL_DIR"
echo "Final wheel: $(ls "$DEST_DIR"/*.whl)"
