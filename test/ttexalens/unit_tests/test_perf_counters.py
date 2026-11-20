# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""Checks the Tensix perf-counter maps against the hardware.

Each test injects a known instruction stream into the Tensix threads of one core through the debug instruction
buffer, with the counter blocks running, and checks that the named counters count exactly that work and that the
counters for other instruction classes, threads, units and stall reasons stay at zero.
"""
import unittest
from typing import Callable

from parameterized import parameterized

from test.ttexalens.unit_tests.test_base import init_cached_test_context
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.debug_tensix import TensixDebug
from ttexalens.device import Device, TensixInstructions
from ttexalens.hardware.perf_counters import TensixPerfCounters

N = 20  # Instructions injected per experiment
# Upper bound on counter reads while waiting for the device to reach a state. Real hardware is almost always there
# after one read, an emulator after a few and a simulator after about ten, so this is far above all of them.
MAX_POLLS = 1000
SEMAPHORE = 1 << 7  # Semaphore mask used by the semaphore stall tests
SRCA, SRCB = 1, 2  # SETDVALID / CLEARDVALID operand bits

# STALLWAIT condition bits. Blackhole renumbers them.
STALLWAIT_CONDITIONS = {
    "wormhole": {
        "thcon_idle": 0,
        "unpack_idle": 1,  # Unpacker 0
        "pack_idle": 3,  # Packer 0
        "math_idle": 7,
        "srca_clear": 8,
        "srcb_clear": 9,
        "srca_valid": 10,
        "srcb_valid": 11,
        "sfpu_idle": 14,
    },
    "blackhole": {
        "thcon_idle": 0,
        "unpack_idle": 1,  # Unpacker 0
        "pack_idle": 3,
        "math_idle": 4,
        "srca_clear": 5,
        "srcb_clear": 6,
        "srca_valid": 7,
        "srcb_valid": 8,
        "sfpu_idle": 11,
    },
}
BLOCK_CFG = 1 << 7  # STALLWAIT / SEMWAIT block mask bit that blocks SETC16
# Backend configuration word holding the first packer's L1 destination address (in 16-byte units).
PACKER_L1_DEST_ADDR_CONFIG = {"wormhole": 57, "blackhole": 69}
PACKER_L1_DEST_ADDR = 0x100000  # Byte address in L1 that the packer test writes to


class TestPerfCounters(unittest.TestCase):
    context: Context
    device: Device
    ops: TensixInstructions
    location: OnChipCoordinate
    tensix_debug: TensixDebug
    perf_counters: TensixPerfCounters
    arch: str

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]
        if cls.device.is_wormhole():
            cls.arch = "wormhole"
        elif cls.device.is_blackhole():
            cls.arch = "blackhole"
        else:
            raise unittest.SkipTest("Instruction injection experiments are written for Wormhole and Blackhole.")
        cls.ops = cls.device.instructions
        cls.location = OnChipCoordinate.create("0,0", device=cls.device)
        perf_counters = cls.location.noc_block.get_perf_counters()
        if perf_counters is None:
            raise unittest.SkipTest("No perf counters on this core.")
        cls.perf_counters = perf_counters
        cls.tensix_debug = TensixDebug(cls.location)

    def setUp(self):
        self.give_back_src_banks()

    def inject(self, instruction: int, thread_id: int, count: int = 1):
        for _ in range(count):
            self.tensix_debug.inject_instruction(instruction, thread_id)

    def give_back_src_banks(self):
        """Gives both banks of SrcA and of SrcB back to the unpackers. CLEARDVALID never waits."""
        for _ in range(2):
            self.inject(self.ops.TT_OP_CLEARDVALID(SRCA | SRCB, 0), 2)

    def wait_for_counter(self, block: str, name: str, condition: Callable[[int], bool], description: str) -> int:
        """Reads counter ``name`` of the running ``block`` until ``condition`` holds for its value and returns that
        value. Waiting on device state instead of for a fixed time works whatever the speed of the device."""
        value = 0
        for _ in range(MAX_POLLS):
            value = self.perf_counters.read_counter(block, name)
            if condition(value):
                return value
        self.fail(f"{name} is {value} after {MAX_POLLS} reads, expected {description}")

    def wait_for_thread_stall(self, thread_id: int):
        """Waits until the thread has been seen stalled."""
        self.wait_for_counter("INSTRN_THREAD", f"thread_stalls_{thread_id}", lambda v: v > 0, "the thread to stall")

    def wait_for_thread_instructions(self, thread_id: int, count: int):
        """Waits until the thread has issued ``count`` instructions."""
        self.wait_for_counter(
            "INSTRN_THREAD", f"thread_instructions_{thread_id}", lambda v: v >= count, f"at least {count}"
        )

    def measure(self, work, blocks: tuple[str, ...]) -> dict[str, int]:
        """Runs ``work`` with ``blocks`` counting and returns every named counter of those blocks."""
        for block in blocks:
            self.perf_counters.reset_block(block)
        work()
        for block in blocks:
            self.perf_counters.stop_block(block)
        values = {}
        for block in blocks:
            for name in self.perf_counters.get_block(block).counters.values():
                values[name] = self.perf_counters.read_counter(block, name)
        return values

    def assertCounters(self, values: dict[str, int], expected: dict[str, int], zero_prefixes: tuple[str, ...]):
        """Counters in ``expected`` must have that value (a negative value means "more than zero"); every other
        counter whose name starts with one of ``zero_prefixes`` must be zero."""
        for name, value in expected.items():
            self.assertIn(name, values, f"no counter named {name}")
            if value < 0:
                self.assertGreater(values[name], 0, name)
            else:
                self.assertEqual(values[name], value, name)
        others = {name: v for name, v in values.items() if name.startswith(zero_prefixes) and name not in expected}
        self.assertEqual({name: v for name, v in others.items() if v != 0}, {})

    def pacr_one_row(self) -> int:
        """PACR that packs one row of Dst to L1 through the first Dst read interface (Blackhole) or packer 0
        (Wormhole). Moves the L1 destination to a free address for the rest of the test."""
        register_store = self.location.noc_block.get_register_store()
        dest_addr, _ = register_store.parse_register_description(f"cfg({PACKER_L1_DEST_ADDR_CONFIG[self.arch]})")
        self.addCleanup(register_store.write_register, dest_addr, register_store.read_register(dest_addr))
        register_store.write_register(dest_addr, PACKER_L1_DEST_ADDR // 16)
        if self.arch == "blackhole":
            return self.ops.TT_OP_PACR(0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1)
        return self.ops.TT_OP_PACR(0, 0, 1, 0, 0, 0, 1)

    def unpacr_nop_zero_src(self, unpacker: int) -> int:
        """UNPACR_NOP that clears the unpacker's SrcA (unpacker 0) or SrcB (unpacker 1) bank to zero."""
        if self.arch == "blackhole":
            return self.ops.TT_OP_UNPACR_NOP(unpacker, 0, 0, 0, 0, 1, 0, 0, 1)
        return self.ops.TT_OP_UNPACR_NOP(unpacker, (1 << 4) | 1)

    @parameterized.expand(
        [
            (instruction_class, thread_id)
            for instruction_class in ("cfg", "sync", "thcon", "math")
            for thread_id in range(3)
        ]
    )
    def test_instruction_class_counters(self, instruction_class: str, thread_id: int):
        instruction = {
            "cfg": self.ops.TT_OP_SETC16(0, 0),
            "sync": self.ops.TT_OP_SEMGET(0),
            "thcon": self.ops.TT_OP_SETDMAREG(0, 0, 0, 0),
            "math": self.ops.TT_OP_SETRWC(0, 0, 0, 0, 0, 0),
        }[instruction_class]
        values = self.measure(lambda: self.inject(instruction, thread_id, N), ("INSTRN_THREAD",))
        self.assertCounters(
            values,
            {f"{instruction_class}_instrn_available_{thread_id}": N, f"thread_instructions_{thread_id}": N},
            ("cfg_", "sync_", "thcon_", "math_", "unpack_", "pack_", "thread_"),
        )

    @parameterized.expand([(unpacker, thread_id) for unpacker in range(2) for thread_id in range(2)])
    def test_unpacker_busy_counters(self, unpacker: int, thread_id: int):
        values = self.measure(
            lambda: self.inject(self.unpacr_nop_zero_src(unpacker), thread_id, N), ("INSTRN_THREAD", "TDMA_UNPACK")
        )
        self.assertCounters(
            values,
            {
                f"unpack_instrn_available_{thread_id}": -1,
                f"thread_instructions_{thread_id}": N,
                f"unpack{unpacker}_busy_thread{thread_id}": -1,
            },
            ("cfg_", "sync_", "thcon_", "math_", "unpack", "pack_", "thread_", "srca_", "srcb_"),
        )

    @parameterized.expand([(src, thread_id) for src in ("srca", "srcb") for thread_id in range(2)])
    def test_src_write_counters(self, src: str, thread_id: int):
        # STOREIND writes four datums from GPRs 8-9 to SrcA or SrcB at the address in GPR 4 plus the offset in the
        # low half of GPR 0; zero all of them first.
        for half_register in (0, 1, 8, 9, 16, 17, 18, 19):
            self.inject(self.ops.TT_OP_SETDMAREG(0, 0, 0, half_register), thread_id)
        storeind = self.ops.TT_OP_STOREIND(0, 0, 1 if src == "srcb" else 0, 0, 0, 8, 4)
        values = self.measure(lambda: self.inject(storeind, thread_id, N), ("TDMA_UNPACK",))
        parity = "even" if thread_id % 2 == 0 else "odd"
        self.assertCounters(
            values,
            {
                f"{src}_write_req": N,
                f"{src}_write_not_blocked_ovr": N,
                f"{src}_write_not_blocked_port": N,
                f"{src}_write_tid_{parity}": N,
            },
            ("srca_", "srcb_", "unpack", "math_"),
        )

    def test_math_counters(self):
        """Each round gives both banks of SrcA and of SrcB to the Matrix Unit, lets one ELWADD consume the Matrix
        Unit's banks, and gives the other banks back, which leaves the bank pointers as they were. This works
        whether or not the unpacker and the Matrix Unit point at the same bank."""

        def work():
            for _ in range(N):
                self.inject(self.ops.TT_OP_SETDVALID(SRCA | SRCB), 0, 2)
                self.inject(self.ops.TT_OP_ELWADD(SRCA | SRCB, 0, 0, 0, 0), 1)
                self.inject(self.ops.TT_OP_CLEARDVALID(SRCA | SRCB, 0), 2)

        values = self.measure(work, ("INSTRN_THREAD", "FPU", "TDMA_UNPACK"))
        self.assertCounters(
            values,
            {
                # CLEARDVALID counts as a math instruction (on thread 2 here); SETDVALID counts in no class.
                "math_instrn_available_1": N,
                "math_instrn_available_2": N,
                "thread_instructions_0": 2 * N,
                "thread_instructions_1": N,
                "thread_instructions_2": N,
                "fpu_counter": N,
                "math_counter": N,  # FPU or SFPU instructions: one per ELWADD
                # Only ELWADD reads SrcA and SrcB; the Matrix Unit starts both ELWADD and CLEARDVALID.
                "math_src_data_ready": N,
                "math_not_d2s_stalled": 2 * N,
                "math_instrn_started": 2 * N,
                "math_instrn_available": 2 * N,
            },
            ("cfg_", "sync_", "thcon_", "math_", "unpack", "pack_", "thread_", "srca_", "srcb_"),
        )

    @parameterized.expand(range(3))
    def test_packer_counters(self, thread_id: int):
        """Each PACR reads Dst and keeps the packer busy for some cycles. How many Dst reads one PACR makes depends on
        packer configuration that the test leaves alone, so only the lower bound is checked."""
        pacr = self.pacr_one_row()

        def work():
            self.inject(pacr, thread_id, N)
            # Let the packer finish: all PACRs issued and its Dst reads requested, granted and no longer growing.
            self.wait_for_thread_instructions(thread_id, N)
            previous = -1

            def settled(requests: int) -> bool:
                nonlocal previous
                granted = self.perf_counters.read_counter("TDMA_PACK", "dest_read_granted_0")
                done = requests >= N and granted == requests and requests == previous
                previous = requests
                return done

            self.wait_for_counter("TDMA_PACK", "packer0_dest_read_req", settled, "all Dst reads to be granted")

        values = self.measure(work, ("INSTRN_THREAD", "TDMA_UNPACK", "TDMA_PACK"))
        self.assertGreaterEqual(values["packer0_dest_read_req"], N)
        self.assertEqual(values["dest_read_granted_0"], values["packer0_dest_read_req"])
        expected = {
            f"pack_instrn_available_{thread_id}": -1,
            f"thread_instructions_{thread_id}": N,
            "packer0_dest_read_req": values["packer0_dest_read_req"],
            "dest_read_granted_0": values["packer0_dest_read_req"],
        }
        # Packer busy: the single packer on Blackhole, packer 0 on Wormhole. On Wormhole, PACRs from threads 0 and 1
        # read one Dst row each and packer 0's busy count for them is not reliably above 0, so on Wormhole busy is
        # checked for thread 2 only and not checked at all for threads 0 and 1.
        if self.arch == "blackhole":
            expected["packer_busy"] = -1
        elif thread_id == 2:
            expected["packer_busy_0"] = -1
        else:
            del values["packer_busy_0"]
        self.assertCounters(
            values,
            expected,
            ("cfg_", "sync_", "thcon_", "math_", "unpack", "pack", "thread_", "srca_", "srcb_", "dest_"),
        )

    @parameterized.expand(
        [(unit, thread_id) for unit in ("thcon", "unpack", "pack", "math", "sfpu") for thread_id in range(3)]
    )
    def test_unit_idle_stall_counters(self, unit: str, thread_id: int):
        """Each round issues one instruction to a unit and then waits on the same thread until that unit is done
        with the thread's instructions, so the thread waits for that unit and nothing else."""
        instruction = {
            "thcon": lambda: self.ops.TT_OP_SETDMAREG(0, 0, 0, 0),
            "unpack": lambda: self.unpacr_nop_zero_src(0),
            "pack": self.pacr_one_row,
            "math": lambda: self.ops.TT_OP_SETRWC(0, 0, 0, 0, 0, 0),
            "sfpu": lambda: self.ops.TT_OP_SFPLOADI(0, 0, 0),
        }[unit]()
        stallwait = self.ops.TT_OP_STALLWAIT(0x1FF, 1 << STALLWAIT_CONDITIONS[self.arch][f"{unit}_idle"])

        def work():
            for _ in range(N):
                self.inject(instruction, thread_id)
                self.inject(stallwait, thread_id)
            self.wait_for_thread_instructions(thread_id, 2 * N)  # Every wait is over

        values = self.measure(work, ("INSTRN_THREAD",))
        self.assertCounters(values, {f"waiting_for_{unit}_idle_{thread_id}": -1}, ("waiting_for_",))

    @parameterized.expand([(thread_id, condition) for thread_id in range(3) for condition in ("nonzero", "nonfull")])
    def test_semaphore_stall_counters(self, thread_id: int, condition: str):
        other_thread = (thread_id + 1) % 3

        def work():
            if condition == "nonzero":
                # Wait while the semaphore is zero, then post it from another thread.
                self.inject(self.ops.TT_OP_SEMINIT(1, 0, SEMAPHORE), thread_id)
                self.inject(self.ops.TT_OP_SEMWAIT(BLOCK_CFG, SEMAPHORE, 1), thread_id)
                release = self.ops.TT_OP_SEMPOST(SEMAPHORE)
            else:
                # Wait while the semaphore is at its maximum, then get it from another thread.
                self.inject(self.ops.TT_OP_SEMINIT(1, 1, SEMAPHORE), thread_id)
                self.inject(self.ops.TT_OP_SEMWAIT(BLOCK_CFG, SEMAPHORE, 2), thread_id)
                release = self.ops.TT_OP_SEMGET(SEMAPHORE)
            self.inject(self.ops.TT_OP_SETC16(0, 0), thread_id)  # Blocked until the wait ends
            self.wait_for_thread_stall(thread_id)
            self.inject(release, other_thread)

        values = self.measure(work, ("INSTRN_THREAD",))
        self.inject(self.ops.TT_OP_SEMINIT(1, 0, SEMAPHORE), thread_id)
        self.assertCounters(
            values,
            {
                f"thread_stalls_{thread_id}": -1,
                f"waiting_for_{condition}_sem_{thread_id}": -1,
                "any_thread_stall": -1,
            },
            ("thread_stalls_", "waiting_for_"),
        )

    @parameterized.expand([("srca", "valid"), ("srcb", "valid"), ("srca", "clear"), ("srcb", "clear")])
    def test_src_stall_counters(self, src: str, condition: str):
        """Thread 0 waits until the Matrix Unit's bank is given to it (valid) or until the unpacker's bank is given
        back (clear); thread 1 ends the wait with SETDVALID or CLEARDVALID. The bank pointers of the unpacker and
        of the Matrix Unit need not match, so up to two of those are needed; neither of them ever waits here."""
        operand = SRCA if src == "srca" else SRCB
        wait_condition = 1 << STALLWAIT_CONDITIONS[self.arch][f"{src}_{condition}"]

        def work():
            if condition == "clear":
                self.inject(self.ops.TT_OP_SETDVALID(operand), 1, 2)
            self.inject(self.ops.TT_OP_STALLWAIT(BLOCK_CFG, wait_condition), 0)
            self.inject(self.ops.TT_OP_SETC16(0, 0), 0)  # Blocked until the wait ends
            self.wait_for_thread_stall(0)
            if condition == "valid":
                self.inject(self.ops.TT_OP_SETDVALID(operand), 1, 2)
            else:
                self.inject(self.ops.TT_OP_CLEARDVALID(operand, 0), 1, 2)

        values = self.measure(work, ("INSTRN_THREAD",))
        self.assertCounters(
            values,
            {"thread_stalls_0": -1, f"waiting_for_{src}_{condition}": -1, "any_thread_stall": -1},
            ("thread_stalls_", "waiting_for_"),
        )


if __name__ == "__main__":
    unittest.main()
