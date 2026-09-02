# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
"""Offline (no device, no simulator) validation of the 4-frame callstack ELF.

Purpose: separate "the ELF/DWARF/unwinder is wrong" from "the Rocket driver
cannot read stack memory". This test drives the *same* native walker that
`lib.callstack` uses (`ttexalens.elf.get_callstack`), but with a synthetic
MemoryAccess that serves the code image and a hand-built stack instead of a
real core. If this passes and the on-sim test still reports one frame, the
fault is in the driver, not in the program or the DWARF.

Why this matters: `MemoryAccess::try_read_word` (ttexalens/cpp/elf/memory_access.hpp:31)
wraps every stack read in `catch (...) { return nullopt; }`, and
callstack.cpp:472 turns a missing return address into `break`. So a broken
memory path produces a SHORT CALLSTACK, never an exception -- a 1-frame result
is indistinguishable from success unless you assert on the depth.

    python3 rocket_callstack_test/test_callstack_offline.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ttexalens.elf import ElfFile, get_callstack  # noqa: E402
from ttexalens._native_ttexalens import MemoryAccess  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ELF = os.path.join(HERE, "callstack_test.elf")
BIN = os.path.join(HERE, "callstack_test.bin")

# Frame layout, read straight off callstack_test.objdump and callstack_test.frames.
# crt0 sets sp=0x40000, then each function does
#   addi sp,sp,-N ; sd ra,N-8(sp) ; sd s0,0(sp) ; addi s0,sp,N
# so at the spin PC the DWARF CFA rule is `DW_CFA_def_cfa: r8 (s0) ofs 0` --
# at -O0 GCC keeps a frame pointer, so the CFA comes from s0, NOT sp. That is
# why the driver must be able to read_gpr(8); reading only sp is not enough.
#
#   frame   sp after prologue   s0 (== CFA)   saved ra @cfa-8   saved s0 @cfa-16
#   main    0x3ffe0             0x40000       0x3fff8 = 0x20    0x3fff0
#   f3      0x3ffd0             0x3ffe0       0x3ffd8 = 0xac    0x3ffd0 = 0x40000
#   f2      0x3ffc0             0x3ffd0       0x3ffc8 = 0x78    0x3ffc0 = 0x3ffe0
#   f1      0x3ffb0             0x3ffc0       0x3ffb8 = 0x4c    0x3ffb0 = 0x3ffd0
#   f1 spins at 0x34
SPIN_PC = 0x34
SP_AT_HALT = 0x3FFB0
S0_AT_HALT = 0x3FFC0
SAVED_RA = {
    0x3FFB8: 0x4C,  # f1 -> f2  (return addr into f2, just after `jal f1`)
    0x3FFC8: 0x78,  # f2 -> f3
    0x3FFD8: 0xAC,  # f3 -> main
    0x3FFF8: 0x20,  # main -> _start
}
# Each slot holds the *caller's* s0, which becomes the caller's CFA.
SAVED_S0 = {
    0x3FFB0: 0x3FFD0,  # f1 saved f2's s0
    0x3FFC0: 0x3FFE0,  # f2 saved f3's s0
    0x3FFD0: 0x40000,  # f3 saved main's s0
    0x3FFE0: 0x00000,  # main saved _start's s0 (unused: we stop on main)
}


class SyntheticStackMemory(MemoryAccess):
    """Serves the flat code image at 0x0 and the hand-built stack above it."""

    def __init__(self, code: bytes):
        super().__init__()
        self._mem = bytearray(4 * 1024 * 1024)  # TL1 is 4 MB at private 0x0
        self._mem[0 : len(code)] = code
        for addr, value in list(SAVED_RA.items()) + list(SAVED_S0.items()):
            self._mem[addr : addr + 8] = value.to_bytes(8, "little")
        self.reads: list[tuple[int, int]] = []

    def read(self, address: int, buffer) -> None:
        size = len(buffer)
        if address < 0 or address + size > len(self._mem):
            raise IndexError(f"read outside TL1: 0x{address:x}+{size}")
        self.reads.append((address, size))
        buffer[:] = self._mem[address : address + size]

    def write(self, address: int, data) -> None:
        self._mem[address : address + len(data)] = bytes(data)

    def read_register(self, register_index: int) -> int:
        if register_index == 2:  # x2 == sp
            return SP_AT_HALT
        if register_index == 8:  # x8 == s0/fp -- this is the CFA register at -O0
            return S0_AT_HALT
        if register_index == 32:  # pc, as read_gpr(32) reports it
            return SPIN_PC
        return 0

    def write_register(self, register_index: int, value: int) -> None:
        raise NotImplementedError


# --- Driver preflight (also hardware-free) ----------------------------------
# `lib.callstack` builds a RiscDebugMemoryAccess with restricted_access=True.
# Every stack read then goes:
#   RiscDebugMemoryAccess.read           (ttexalens/memory_access.py:148)
#     -> _validate_access                (:175)  -> risc_debug.get_l1()
#     -> risc_debug.ensure_private_memory_access()
# QuasarRocketCoreDebug overrides NEITHER, so both land on the abstract
# RocketCoreDebug versions that `raise NotImplementedError`. try_read_word
# swallows that, so the callstack silently stops at frame 0.
REQUIRED_OVERRIDES = ("get_l1", "get_data_private_memory", "ensure_private_memory_access", "can_debug")


def check_driver_overrides() -> list[str]:
    """Return the names QuasarRocketCoreDebug still inherits as NotImplementedError."""
    from ttexalens.hardware.rocket_core_debug import RocketCoreDebug
    from ttexalens.hardware.quasar.rocket_core_debug import QuasarRocketCoreDebug

    missing = []
    for name in REQUIRED_OVERRIDES:
        base = getattr(RocketCoreDebug, name, None)
        derived = getattr(QuasarRocketCoreDebug, name, None)
        if base is not None and derived is base:
            missing.append(name)
    return missing


def report_driver_overrides() -> bool:
    missing = check_driver_overrides()
    if missing:
        print("driver preflight: MISSING overrides on QuasarRocketCoreDebug -> " + ", ".join(missing))
        print("  a multi-frame callstack is IMPOSSIBLE until these are implemented;")
        print("  see rocket_callstack_test/README.md and quasar_rocket_callstack_prereq.patch")
        return False
    print("driver preflight: all required overrides present")
    return True


def main() -> int:
    for path in (ELF, BIN):
        if not os.path.exists(path):
            print(f"FAIL: {path} missing -- run rocket_callstack_test/build_in_docker.sh first")
            return 1

    with open(BIN, "rb") as f:
        code = f.read()
    elf = ElfFile(ELF)
    mem = SyntheticStackMemory(code)

    cs = get_callstack([elf], SPIN_PC, mem, 100, "main", extract_variables=False)

    print(f"callstack ({len(cs)} frames) from pc=0x{SPIN_PC:x}, sp=0x{SP_AT_HALT:x}")
    for i, frame in enumerate(cs):
        pc = "?" if frame.pc is None else f"0x{frame.pc:08x}"
        fi = frame.file_info
        where = f"{os.path.basename(fi.file)}:{fi.line}" if fi else "?"
        cfa = "?" if frame.cfa is None else f"0x{frame.cfa:x}"
        print(f"  #{i} {pc} in {frame.function_name} at {where}  cfa={cfa}")

    names = [f.function_name for f in cs]
    failures = []
    if len(cs) < 4:
        failures.append(f"expected >= 4 frames, got {len(cs)} -- DWARF/unwinder problem in the ELF itself")
    if names[:4] != ["f1", "f2", "f3", "main"]:
        failures.append(f"expected ['f1','f2','f3','main'], got {names[:4]}")
    if cs and (cs[0].file_info is None or not cs[0].file_info.file.endswith("main.cc")):
        failures.append(f"frame #0 file_info={cs[0].file_info and cs[0].file_info.file}, expected .../main.cc")
    if cs and cs[0].pc != SPIN_PC:
        failures.append(f"frame #0 pc=0x{cs[0].pc:x}, expected 0x{SPIN_PC:x}")

    driver_ok = report_driver_overrides()

    if failures:
        print("\n==== FAILED ====")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"\n==== PASS ==== ({len(mem.reads)} synthetic memory reads)")
    if not driver_ok:
        print("NOTE: the ELF unwinds correctly, but the live driver cannot read the stack yet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
