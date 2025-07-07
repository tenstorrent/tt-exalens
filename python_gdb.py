# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
import tempfile
import subprocess
import os

# ---- Input Variables (set these as needed) ----
PORT = 6767  # Replace with your actual port
PID = 13  # Replace with actual process ID
ELF = "/home/adjordjevic/.cache/tt-metal-cache/474011dcd8/4098/kernels/erisc_print/8333010637973881611/idle_erisc/idle_erisc.elf"  # Replace with actual ELF path
OFFSET = 29648  # Replace with actual offset

# ---- GDB Executable Path ----
GDB_PATH = "./build/sfpi/compiler/bin/riscv32-tt-elf-gdb"

# ---- Create Temporary GDB Script ----
with tempfile.NamedTemporaryFile(mode="w", suffix=".gdb", delete=False) as gdb_script:
    gdb_script_path = gdb_script.name
    gdb_script.write(
        f"""\
set pagination off
set confirm off
shell > gdb.output
set logging file gdb.output

target extended-remote localhost:{PORT}
python
try:
    gdb.execute("attach {PID}")
except gdb.error as e:
    print(e)
end

python
try:
    gdb.execute("add-symbol-file {ELF} {OFFSET}")
except gdb.error as e:
    print(e)
end

set logging enabled on
bt
set logging enabled off

python
try:
    gdb.execute("detach")
except gdb.error as e:
    print("Detach failed:", e)
end

q
"""
    )

# ---- Run GDB with Script ----
subprocess.run([GDB_PATH, "-x", gdb_script_path])

# ---- Clean Up ----
os.remove(gdb_script_path)
