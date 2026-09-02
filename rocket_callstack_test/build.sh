#!/usr/bin/env bash
# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
#
# Build the 4-frame callstack test ELF for a Quasar Rocket (RV64) core.
#
# Same recipe as the (reverted) rocket_pattern_demo/build.sh -- tt-metal's
# Rocket/DM compile line with the tt-metal-specific bits stripped -- with one
# deliberate change: -O0 instead of -Os, so the f1/f2/f3/main chain survives as
# four real frames instead of being inlined or tail-called away.
#
# -fno-asynchronous-unwind-tables together with -g is what puts the unwind info
# in .debug_frame (link.ld DISCARDs .eh_frame), which is what the callstack
# walker reads.
#
# The prebuilt sfpi binaries need glibc >= 2.33, so on a RHEL8 host run this
# inside the Ubuntu container -- see build_in_docker.sh.
set -euo pipefail
cd "$(dirname "$0")"

SFPI=../build_riscv/sfpi/compiler/bin
CXX="$SFPI/riscv-tt-elf-g++"
OBJCOPY="$SFPI/riscv-tt-elf-objcopy"
OBJDUMP="$SFPI/riscv-tt-elf-objdump"
READELF="$SFPI/riscv-tt-elf-readelf"

ARCH="-mcpu=tt-qsr64-rocc -mabi=lp64 -mcmodel=medany"
CFLAGS="$ARCH -O0 -g -ffreestanding -fno-asynchronous-unwind-tables -fno-exceptions -fno-rtti -nostdlib"

"$CXX" $CFLAGS -c main.cc -o main.o
"$CXX" $CFLAGS -c crt0.S -o crt0.o
"$CXX" $CFLAGS -nostartfiles -Wl,--no-warn-rwx-segments -T link.ld crt0.o main.o -o callstack_test.elf

"$OBJCOPY" -O binary callstack_test.elf callstack_test.bin
"$OBJDUMP" -d callstack_test.elf > callstack_test.objdump
"$READELF" --debug-dump=frames callstack_test.elf > callstack_test.frames
"$READELF" --debug-dump=decodedline callstack_test.elf > callstack_test.lines

echo "built callstack_test.elf ($(stat -c%s callstack_test.elf) bytes), callstack_test.bin ($(stat -c%s callstack_test.bin) bytes)"

# Offline gate: fail the build if the ELF cannot possibly produce 4 frames.
# Cheaper to catch here than to burn a simulator boot on it.
missing=""
for fn in f1 f2 f3 main; do
    grep -qE "^ *[0-9a-f]+ <$fn>:" callstack_test.objdump || missing="$missing $fn(sym)"
    grep -q "FDE .*pc=" callstack_test.frames || true
done
if [ -n "$missing" ]; then
    echo "FAIL: missing symbols:$missing" >&2
    exit 1
fi
nfde=$(grep -c "^ *[0-9a-f]* [0-9a-f]* [0-9a-f]* FDE" callstack_test.frames || true)
echo "FDE count in .debug_frame: $nfde (need >= 4: f1 f2 f3 main)"
if [ "${nfde:-0}" -lt 4 ]; then
    echo "FAIL: fewer than 4 FDEs -- unwinding cannot reach main" >&2
    exit 1
fi
echo "offline checks OK"
