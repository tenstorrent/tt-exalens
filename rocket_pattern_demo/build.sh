#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
#
# Build a minimal bare-metal pattern-writer ELF for a Quasar Rocket (RV64) core.
#
# This is tt-metal's Rocket/DM compile recipe with everything tt-metal-specific
# stripped out. Removed vs. tt-metal's DM kernel link line:
#   - TT compiler extensions:  -ftt-nttp -ftt-constinit -ftt-consteval
#   - TT codegen tweaks:        -mno-tt-tensix-optimize-replay, --emit-relocs
#   - TLS startup model:        -fno-extern-tls-init -ftls-model=local-exec
#   - all tt_metal/... include paths and the ARCH_QUASAR define
#   - the generated kernel_dm.ld linker script + its __kn_text/__tls_size/...
#     defsyms, and the prebuilt tt-qsr64-crt0-tls.o / tt-qsr64-noc.o /
#     tt-qsr64-substitutes.o objects
# What's left is just: compile the simple C++ -> object, then link it (with our
# own crt0 + linker script) into an ELF.
set -euo pipefail
cd "$(dirname "$0")"

SFPI=../build_riscv/sfpi/compiler/bin
CXX="$SFPI/riscv-tt-elf-g++"
OBJCOPY="$SFPI/riscv-tt-elf-objcopy"
OBJDUMP="$SFPI/riscv-tt-elf-objdump"

# Rocket core = RV64, qsr64 multilib (lp64). -mcpu=tt-qsr64-rocc is tt-metal's
# Rocket/DM target CPU; -mcmodel=medany lets the code reach the uncached L1 alias.
ARCH="-mcpu=tt-qsr64-rocc -mabi=lp64 -mcmodel=medany"
CFLAGS="$ARCH -Os -g -ffreestanding -fno-asynchronous-unwind-tables -fno-exceptions -fno-rtti -nostdlib"

# 1) compile the simple C++ into an object
"$CXX" $CFLAGS -c main.cc -o main.o
# (assemble our startup)
"$CXX" $CFLAGS -c crt0.S -o crt0.o
# 2) link the object(s) into the ELF
"$CXX" $CFLAGS -nostartfiles -Wl,--no-warn-rwx-segments -T link.ld crt0.o main.o -o pattern.elf

# Flat image for the NoC loader (pyelftools is not available in /opt/venv, so the
# loader writes one contiguous blob at 0x0 instead of parsing PT_LOAD segments).
"$OBJCOPY" -O binary pattern.elf pattern.bin
"$OBJDUMP" -d pattern.elf > pattern.objdump

echo "built pattern.elf ($(stat -c%s pattern.elf) bytes), pattern.bin ($(stat -c%s pattern.bin) bytes)"
