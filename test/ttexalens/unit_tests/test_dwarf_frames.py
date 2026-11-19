# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Device-free tests of call-frame unwinding over a hand-built register and stack image.
"""
import unittest

from test.ttexalens.unit_tests.compiled_elf import ElfImageMemoryAccess, compile_elf
from ttexalens.elf import DwarfAttributeTag, DwarfDieTag, ElfFile, FrameInspection, FrameSnapshot, get_callstack

# `vla_caller` has a variable-length array, so its CFA is defined on the frame pointer (s0). It
# calls `leaf`, which has no frame of its own and never touches s0, and `main` calls it in a
# non-tail position so all three frames are on the stack while `leaf` runs.
FRAME_POINTER_SOURCE = """
volatile int g_sink;

__attribute__((noinline)) int leaf(int x) {
    asm volatile("ebreak");
    return x + 1;
}

__attribute__((noinline)) int vla_caller(int n) {
    volatile int buf[n];
    for (int i = 0; i < n; i++) buf[i] = i;
    int r = leaf(buf[n - 1]);
    g_sink = buf[0];
    return r;
}

int main() {
    g_sink = vla_caller(g_sink + 4);
    return 0;
}
"""

REG_RA = 1
REG_SP = 2
REG_S0 = 8


class TestDwarfFrames(unittest.TestCase):
    elf: ElfFile

    @classmethod
    def setUpClass(cls):
        cls.elf = ElfFile(compile_elf(FRAME_POINTER_SOURCE, ["-O2", "-g"]))

    def function_address(self, name: str) -> int:
        die = self.elf.find_die_by_name(name)
        assert die is not None and die.tag == DwarfDieTag.subprogram, name
        low_pc = die.get_attribute(DwarfAttributeTag.low_pc)
        assert low_pc is not None and isinstance(low_pc.value, int), name
        return low_pc.value

    def call_return_pc(self, caller: str) -> int:
        die = self.elf.find_die_by_name(caller)
        assert die is not None, caller
        child = die.get_first_child()
        while child is not None:
            if child.tag == DwarfDieTag.call_site:
                return_pc = child.get_attribute(DwarfAttributeTag.call_return_pc)
                assert return_pc is not None and isinstance(return_pc.value, int)
                return return_pc.value
            child = child.get_next_sibling()
        raise AssertionError(f"no call site in {caller}")

    def test_outer_frame_sp_is_child_cfa(self):
        """An outer frame's sp is the CFA of the frame it called, not the live sp."""
        live_sp = 0x8000
        child_cfa = 0x8040
        leaf_pc = self.function_address("leaf")
        caller_pc = self.call_return_pc("vla_caller") - 1
        mem = ElfImageMemoryAccess(self.elf, {REG_SP: live_sp})
        leaf_fde = self.elf.get_frame_description(leaf_pc, mem)
        caller_fde = self.elf.get_frame_description(caller_pc, mem)
        assert leaf_fde is not None and caller_fde is not None
        leaf_frame = FrameSnapshot(leaf_fde, child_cfa, leaf_pc)
        caller_frame = FrameSnapshot(caller_fde, 0x9000, caller_pc)

        self.assertEqual(FrameInspection(mem, leaf_frame, []).read_register(REG_SP), live_sp)
        self.assertEqual(FrameInspection(mem, caller_frame, [leaf_frame]).read_register(REG_SP), child_cfa)

    def test_frame_pointer_caller_of_frameless_leaf(self):
        """The walk recovers a frame-pointer-based CFA from the live frame pointer when the callee left it alone."""
        leaf_pc = self.function_address("leaf")
        return_into_caller = self.call_return_pc("vla_caller")
        return_into_main = self.call_return_pc("main")

        live_sp = 0x8000  # leaf has no frame: its CFA is this sp
        frame_pointer = 0x8040  # vla_caller's s0 == its CFA; the array lies between the two
        mem = ElfImageMemoryAccess(self.elf, {REG_RA: return_into_caller, REG_SP: live_sp, REG_S0: frame_pointer})
        # vla_caller's save area just below its CFA: ra at CFA-4, main's s0 at CFA-8.
        mem.write_word(frame_pointer - 4, return_into_main)
        mem.write_word(frame_pointer - 8, 0x11111111)
        # The word at the leaf's CFA-8 is stale stack data, not the caller's frame pointer.
        mem.write_word(live_sp - 8, 0xDEAD0000)

        callstack = get_callstack([self.elf], leaf_pc, mem, extract_variables=False)

        self.assertEqual([entry.function_name for entry in callstack], ["leaf", "vla_caller", "main"])
        self.assertEqual(callstack[1].cfa, frame_pointer)
        self.assertEqual(callstack[2].cfa, frame_pointer + 16)


if __name__ == "__main__":
    unittest.main()
