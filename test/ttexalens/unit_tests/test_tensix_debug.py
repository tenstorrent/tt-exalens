# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import math
import unittest
from typing import Callable
from parameterized import parameterized_class, parameterized
import tt_umd
from test.ttexalens.unit_tests.test_base import init_cached_test_context

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.debug_tensix import TensixDebug, TILE_SIZE, TensixDataFormat, REGFILE
from ttexalens.device import TensixInstructions
from ttexalens.exceptions import TTException


@parameterized_class(
    [
        {"location_str": "0,0"},
        {"location_str": "1,1"},
        {"location_str": "2,2"},
    ]
)
class TestTensixDebug(unittest.TestCase):
    context: Context
    location: OnChipCoordinate
    tensix_debug: TensixDebug
    location_str: str
    ops: TensixInstructions
    debug_bus: DebugBusSignalStore

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.ops = cls.context.devices[0].instructions

    def setUp(self):
        self.location = OnChipCoordinate.create(self.location_str, device=self.context.devices[0])
        self.tensix_debug = TensixDebug(self.location)
        assert self.location.noc_block.debug_bus is not None
        self.debug_bus = self.location.noc_block.debug_bus

    def is_blackhole(self) -> bool:
        return self.location.device._arch == tt_umd.ARCH.BLACKHOLE

    @parameterized.expand(
        [
            1,
            2,
            4,
            8,
            (1, float(0.0)),
            (1, float(-0.0)),
            (1, float("inf")),
            (1, float("-inf")),
            (1, float("nan")),
        ]
    )
    def test_read_write_regfile_fp32(self, num_tiles: int, value: float | None = None):
        if not self.is_blackhole():
            self.skipTest("Direct read/write is supported only on Blackhole.")

        regfile = REGFILE.DSTACC  # Writing is only supported for dest

        step = 0.01
        error_threshold = 1e-4
        num_of_elements = num_tiles * TILE_SIZE
        if value is None:
            data = [step * i - step * num_of_elements / 2 for i in range(num_of_elements)]
        else:
            data = [value for _ in range(num_of_elements)]
        self.tensix_debug.write_regfile(regfile, data, TensixDataFormat.Float32)
        ret = self.tensix_debug.read_regfile(regfile, num_tiles)
        if value is None:
            assert len(ret) == len(data)
            assert all(abs(a - b) < error_threshold for a, b in zip(ret, data) if isinstance(a, float))
        elif math.isnan(value):
            assert all(math.isnan(a) for a in ret if isinstance(a, float))
        else:
            assert ret == data

    @parameterized.expand(
        [
            1,
            2,
            4,
            8,
        ]
    )
    def test_read_write_regfile_int32(self, num_tiles: int, value: int | None = None):
        if not self.is_blackhole():
            self.skipTest("Direct read/write is supported only on Blackhole.")

        regfile = REGFILE.DSTACC  # Writing is only supported for dest

        num_of_elements = num_tiles * TILE_SIZE
        min_value = -(2**31)
        max_value = 2**31 - 1
        data = [min_value] + [i - num_of_elements // 2 for i in range(1, num_of_elements - 1)] + [max_value]
        self.tensix_debug.write_regfile(regfile, data, TensixDataFormat.Int32)
        assert self.tensix_debug.read_regfile(regfile, num_tiles) == data

    @parameterized.expand(
        [
            1,
            2,
            4,
            8,
        ]
    )
    def test_read_write_regfile_uint32(self, num_tiles: int):
        if not self.is_blackhole():
            self.skipTest("Direct read/write is supported only on Blackhole.")

        regfile = REGFILE.DSTACC  # Writing is only supported for dest

        num_of_elements = num_tiles * TILE_SIZE
        max_value = 2**32 - 1
        data = [i for i in range(num_of_elements - 1)] + [max_value]
        self.tensix_debug.write_regfile(regfile, data, TensixDataFormat.UInt32)
        assert self.tensix_debug.read_regfile(regfile, num_tiles, signed=False) == data

    @parameterized.expand(
        [
            1,
            2,
            4,
            8,
        ]
    )
    def test_read_write_regfile_int8(self, num_tiles: int):
        if not self.is_blackhole():
            self.skipTest("Direct read/write is supported only on Blackhole.")

        regfile = REGFILE.DSTACC  # Writing is only supported for dest

        num_of_elements = num_tiles * TILE_SIZE
        data = [(i % 2**8) - 2**7 for i in range(num_of_elements)]
        self.tensix_debug.write_regfile(regfile, data, TensixDataFormat.Int8)
        assert self.tensix_debug.read_regfile(regfile, num_tiles) == data

    @parameterized.expand(
        [
            1,
            2,
            4,
            8,
        ]
    )
    def test_read_write_regfile_uint8(self, num_tiles: int):
        if not self.is_blackhole():
            self.skipTest("Direct read/write is supported only on Blackhole.")

        regfile = REGFILE.DSTACC  # Writing is only supported for dest

        num_of_elements = num_tiles * TILE_SIZE
        data = [(i % 2**8) for i in range(num_of_elements)]
        self.tensix_debug.write_regfile(regfile, data, TensixDataFormat.UInt8)
        assert self.tensix_debug.read_regfile(regfile, num_tiles, signed=False) == data

    @parameterized.expand(
        [
            (TensixDataFormat.UInt16,),  # Unsupported data format
            (TensixDataFormat.Float16,),  # Unsupported data format
            (TensixDataFormat.Float16_b,),  # Unsupported data format
            (TensixDataFormat.Bfp8,),  # Unsupported data format
            (TensixDataFormat.Int32, REGFILE.DSTACC, 2**31),  # Value out of range for Int32
            (TensixDataFormat.Int32, REGFILE.DSTACC, -(2**31 + 1)),  # Value out of range for Int32
            (TensixDataFormat.Int8, REGFILE.DSTACC, 2**7),  # Value out of range for Int8
            (TensixDataFormat.Int8, REGFILE.DSTACC, -(2**7 + 1)),  # Value out of range for Int8
            (TensixDataFormat.Float32, REGFILE.SRCA),  # srcA not supported
            (TensixDataFormat.Float32, REGFILE.SRCB),  # srcB not supported
        ]
    )
    def test_invalid_write_regfile(
        self, df: TensixDataFormat, regfile: int | str | REGFILE = REGFILE.DSTACC, value: int | float = 1
    ):
        if not self.is_blackhole():
            self.skipTest("Direct read/write is supported only on Blackhole.")

        with self.assertRaises((TTException, ValueError)):
            self.tensix_debug.write_regfile(regfile, [value], df)

    def _read_signal(self, signal_name: str) -> int:
        if signal_name in self.debug_bus.signal_names:
            return self.debug_bus.read_signal(signal_name)
        elif signal_name in self.debug_bus.combined_signals:
            signals = sorted(self.debug_bus.combined_signals[signal_name], reverse=True)
            value = 0
            for signal in signals:
                signal_desc = self.debug_bus.get_signal_description(signal)
                value = value << bin(signal_desc.mask).count("1")
                value |= self.debug_bus.read_signal(signal_desc)
            return value
        else:
            raise ValueError(f"Signal {signal_name} not found.")

    @parameterized.expand(
        [
            ([1, 2, 3], [4, 5, 6], [7, 8, 9]),
            ([0, 0, 0], [0, 0, 0], [0, 0, 0]),
            ([0xF, 0xF, 0xF], [0xF, 0xF, 0xF], [0xF, 0xF, 0xF]),
        ]
    )
    def test_register_window_counters(self, rwc_a: list[int], rwc_b: list[int], rwc_dst: list[int]):
        for thread_id in range(3):
            # 0x7 is code for setting all three RWCs for that thread
            self.tensix_debug.inject_instruction(
                self.ops.TT_OP_SETRWC(0, 0, rwc_dst[thread_id], rwc_b[thread_id], rwc_a[thread_id], 0x7), thread_id
            )
            self.assertEqual(self._read_signal(f"rwc{thread_id}_srca"), rwc_a[thread_id])
            self.assertEqual(self._read_signal(f"rwc{thread_id}_srcb"), rwc_b[thread_id])
            self.assertEqual(self._read_signal(f"rwc{thread_id}_dst"), rwc_dst[thread_id])

    @parameterized.expand(
        [
            # (register, SETDVALID / CLEARDVALID operand bit, signal names without the group prefix)
            (
                "srca",
                0x1,
                "unpacker0_srca_bank",
                "mxu_srca_bank",
                ["srca_srca_bank0_mxu_allowed", "srca_bank1_mxu_allowed"],
                "srca_mxu_allowed",
                "srca_unpacker0_allowed",
            ),
            (
                "srcb",
                0x2,
                "unpacker1_srcb_bank",
                "mxu_srcb_bank",
                ["srcb_bank0_mxu_allowed", "srcb_bank1_mxu_allowed"],
                "srcb_mxu_allowed",
                "srcb_unpacker1_allowed",
            ),
        ]
    )
    def test_src_access_control_signals(
        self,
        _register: str,
        operand: int,
        unpacker_bank: str,
        mxu_bank: str,
        bank_mxu_allowed: list[str],
        mxu_allowed: str,
        unpacker_allowed: str,
    ):
        """SETDVALID gives the unpacker's bank to the matrix unit and CLEARDVALID gives the matrix unit's bank back.
        The access control signals of SrcA and of SrcB must follow both."""
        prefix = "srca_srcb_access_control_"
        if prefix + unpacker_bank not in self.debug_bus.signal_names:
            self.skipTest("Debug bus has no SrcA/SrcB access control signals on this device.")

        def read(signal_name: str) -> int:
            return self._read_signal(prefix + signal_name)

        # State of the register: (unpacker's bank, matrix unit's bank, bank 0 given, bank 1 given),
        # where "given" means that the matrix unit is allowed to use the bank.
        def read_state() -> tuple[int, int, int, int]:
            return (read(unpacker_bank), read(mxu_bank), read(bank_mxu_allowed[0]), read(bank_mxu_allowed[1]))

        def state_after(state: tuple[int, int, int, int], instruction: str) -> tuple[int, int, int, int]:
            unpacker, mxu, *given = state
            if instruction == "SETDVALID":
                given[unpacker] = 1
                unpacker ^= 1
            else:
                given[mxu] = 0
                mxu ^= 1
            return (unpacker, mxu, given[0], given[1])

        def inject(instruction: str):
            op = (
                self.ops.TT_OP_SETDVALID(operand)
                if instruction == "SETDVALID"
                else self.ops.TT_OP_CLEARDVALID(operand, 0)
            )
            self.tensix_debug.inject_instruction(op, 0)

        def go_to(target: tuple[int, int, int, int]):
            """Injects the shortest sequence of instructions that takes the register to the target state."""
            paths: dict[tuple[int, int, int, int], list[str]] = {read_state(): []}
            queue = list(paths)
            while queue and target not in paths:
                state = queue.pop(0)
                for instruction in ("SETDVALID", "CLEARDVALID"):
                    if instruction == "SETDVALID" and state[2 + state[0]]:
                        continue  # SETDVALID waits while the matrix unit holds the unpacker's bank.
                    next_state = state_after(state, instruction)
                    if next_state not in paths:
                        paths[next_state] = paths[state] + [instruction]
                        queue.append(next_state)
            # The only states that cannot be reached are the two in which the unpacker waits for a bank
            # that the matrix unit, being on the other bank, never gives back.
            for instruction in paths.get(target, []):
                inject(instruction)

        # Leave the register as it was found, also if a check fails.
        initial_state = read_state()
        self.addCleanup(go_to, initial_state)

        def check(state: tuple[int, int, int, int], step: str):
            unpacker, mxu, *given = state
            expected = {
                unpacker_bank: unpacker,
                mxu_bank: mxu,
                bank_mxu_allowed[0]: given[0],
                bank_mxu_allowed[1]: given[1],
                mxu_allowed: given[mxu],
                unpacker_allowed: 1 - given[unpacker],
            }
            actual = {signal_name: read(signal_name) for signal_name in expected}
            self.assertEqual(actual, expected, f"after {step}")

        # Start with both banks given back.
        state = initial_state
        while state[2] or state[3]:
            inject("CLEARDVALID")
            state = state_after(state, "CLEARDVALID")
        check(state, "giving back both banks")

        # Two rounds, so that each bank is given and given back once.
        for round_id in range(2):
            for instruction in ("SETDVALID", "CLEARDVALID"):
                inject(instruction)
                state = state_after(state, instruction)
                check(state, f"{instruction}, round {round_id}")

    def _reset_register_window_counters(self):
        for thread_id in range(3):
            # 0xF sets SrcA, SrcB, Dst and the fidelity phase of that thread to 0
            self.tensix_debug.inject_instruction(self.ops.TT_OP_SETRWC(0, 0, 0, 0, 0, 0xF), thread_id)

    def test_dst_register_window_counter_width(self):
        """The Dst counter and its carriage-return copy keep 12 bits; the signals must show all of them."""
        if self.is_blackhole():
            self.skipTest("Checks the Wormhole Dst counter width.")

        self.addCleanup(self._reset_register_window_counters)
        for thread_id in range(3):
            self._reset_register_window_counters()
            value = 0
            for target in [0x3FF, 0x400, 0x7FF, 0xFFF]:
                while value < target:
                    step = min(target - value, 0xF)
                    # rwc_cr = 0x4: increment Dst_Cr and set Dst to it
                    self.tensix_debug.inject_instruction(self.ops.TT_OP_INCRWC(0x4, step, 0, 0), thread_id)
                    value += step
                self.assertEqual(self._read_signal(f"rwc{thread_id}_dst"), value, f"thread {thread_id}")
                self.assertEqual(self._read_signal(f"rwc{thread_id}_dst_cr"), value, f"thread {thread_id}")

    def test_fidelity_phase_signals(self):
        """Each thread's fidelity phase is shown by its own signal."""
        if self.is_blackhole() or "rwc0_fidelity_phase" not in self.debug_bus.signal_names:
            self.skipTest("Test uses Wormhole ADDR_MOD register numbers.")

        # Wormhole ADDR_MOD_AB_SEC, ADDR_MOD_DST_SEC and ADDR_MOD_BIAS_SEC register numbers of address modes 3 and 7.
        # Address mode 7 is what address mode 3 selects when ADDR_MOD_SET_Base is set.
        address_mode_registers = [(13, 26, 51), (21, 30, 55)]
        fidelity_increment_1 = 1 << 13

        def write_address_modes(dst_value: int):
            for thread_id in range(3):
                for ab, dst, bias in address_mode_registers:
                    self.tensix_debug.inject_instruction(self.ops.TT_OP_SETC16(ab, 0), thread_id)
                    self.tensix_debug.inject_instruction(self.ops.TT_OP_SETC16(dst, dst_value), thread_id)
                    self.tensix_debug.inject_instruction(self.ops.TT_OP_SETC16(bias, 0), thread_id)

        def increment_fidelity_phase(thread_id: int):
            # ZEROACC on row 0xFF in 16-row mode clears nothing and applies address mode 3
            self.tensix_debug.inject_instruction(self.ops.TT_OP_ZEROACC(1, 3, 0xFF), thread_id)

        def check(phases: list[int]):
            actual = [self._read_signal(f"rwc{thread_id}_fidelity_phase") for thread_id in range(3)]
            self.assertEqual(actual, phases)

        self.addCleanup(write_address_modes, 0)
        self.addCleanup(self._reset_register_window_counters)
        self._reset_register_window_counters()
        write_address_modes(fidelity_increment_1)
        check([0, 0, 0])
        for thread_id in range(3):
            for _ in range(thread_id + 1):
                increment_fidelity_phase(thread_id)
        check([1, 2, 3])
        increment_fidelity_phase(0)
        check([2, 2, 3])
        increment_fidelity_phase(2)
        check([2, 2, 0])

    def test_register_window_counter_carriage_returns(self):
        """Each thread's SrcA and SrcB counters and their carriage-return copies are shown by their own signals."""
        self.addCleanup(self._reset_register_window_counters)
        self._reset_register_window_counters()
        expected = {}
        for thread_id in range(3):
            srca_cr, srcb_cr = 3 + 4 * thread_id, 5 + 4 * thread_id
            # SETRWC sets each counter and its carriage-return copy; INCRWC then moves only the counters
            self.tensix_debug.inject_instruction(self.ops.TT_OP_SETRWC(0, 0, 0, srcb_cr, srca_cr, 0x3), thread_id)
            self.tensix_debug.inject_instruction(self.ops.TT_OP_INCRWC(0, 0, 2 + thread_id, 1 + thread_id), thread_id)
            expected[f"rwc{thread_id}_srca"] = srca_cr + 1 + thread_id
            expected[f"rwc{thread_id}_srca_cr"] = srca_cr
            expected[f"rwc{thread_id}_srcb"] = srcb_cr + 2 + thread_id
            expected[f"rwc{thread_id}_srcb_cr"] = srcb_cr
        actual = {signal_name: self._read_signal(signal_name) for signal_name in expected}
        self.assertEqual(actual, expected)

    def test_last_math_instruction_signals(self):
        """The last math instruction and the thread that issued it."""
        if not self.is_blackhole():
            self.skipTest("Test uses the Blackhole ZEROACC encoding and signal names.")

        # Blackhole ZEROACC takes (clear_mode, use_32_bit_mode, clear_zero_flags, addr_mode, where)
        zeroacc: Callable[..., int] = self.ops.TT_OP_ZEROACC
        for thread_id in [1, 2, 0]:
            # ZEROACC on a row above 0xF0 in 16-row mode clears nothing
            instruction = zeroacc(1, 0, 0, thread_id, 0xFF - thread_id)
            self.tensix_debug.inject_instruction(instruction, thread_id)
            if isinstance(instruction, (bytes, bytearray)):
                instruction = int.from_bytes(instruction, "little")
            self.assertEqual(self._read_signal("rwc_last_math_instrn"), instruction)
            self.assertEqual(self._read_signal("rwc_last_math_winner_thread"), thread_id)

    def test_idle_instruction_buffers_are_empty(self):
        """No thread of an idle core has instructions waiting."""
        signal_names = [f"tensix_frontend_t{thread_id}_ibuffer_empty_raw" for thread_id in range(3)]
        if any(signal_name not in self.debug_bus.signal_names for signal_name in signal_names):
            self.skipTest("Debug bus has no instruction buffer signals on this device.")

        self.assertEqual([self._read_signal(signal_name) for signal_name in signal_names], [1, 1, 1])
