# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import math
import unittest
from parameterized import parameterized_class, parameterized
from test.ttexalens.unit_tests.test_base import init_cached_test_context

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.debug_tensix import TensixDebug, TILE_SIZE, TensixDataFormat, REGFILE
from ttexalens.exceptions import TTException


@parameterized_class(
    [
        {"location_str": "0,0", "neo_id": None},
        {"location_str": "1,1", "neo_id": None},
        {"location_str": "2,2", "neo_id": None},
        {"location_str": "0,0", "neo_id": 0},
        {"location_str": "0,0", "neo_id": 3},
    ]
)
class TestTensixDebug(unittest.TestCase):
    context: Context
    location: OnChipCoordinate
    tensix_debug: TensixDebug
    location_str: str
    neo_id: int | None
    debug_bus: DebugBusSignalStore

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()

    def setUp(self):
        self.location = OnChipCoordinate.create(self.location_str, device=self.context.devices[0])
        if self.neo_id is not None and self.neo_id not in self.location.noc_block.neo_ids:
            self.skipTest(f"NEO {self.neo_id} is not available on this platform.")

        tensix_debug = self.location.noc_block.get_tensix_debug(self.neo_id)
        if tensix_debug is None:
            self.skipTest(f"There is no Tensix at {self.location.to_user_str(self.neo_id)}.")
        self.tensix_debug = tensix_debug
        debug_bus = self.location.noc_block.get_debug_bus(self.neo_id)
        assert debug_bus is not None
        self.debug_bus = debug_bus

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
        if self.tensix_debug.dest is None:
            self.skipTest("Direct read/write of dest is not supported on this device.")

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
        if self.tensix_debug.dest is None:
            self.skipTest("Direct read/write of dest is not supported on this device.")

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
        if self.tensix_debug.dest is None:
            self.skipTest("Direct read/write of dest is not supported on this device.")

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
        if self.tensix_debug.dest is None:
            self.skipTest("Direct read/write of dest is not supported on this device.")

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
        if self.tensix_debug.dest is None:
            self.skipTest("Direct read/write of dest is not supported on this device.")

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
        if self.tensix_debug.dest is None:
            self.skipTest("Direct read/write of dest is not supported on this device.")

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
                value = value << signal_desc.mask.bit_length()
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
        if self.location.device.is_quasar():
            self.skipTest("Tensix instructions are not available on Quasar.")
        ops = self.location.device.instructions
        for thread_id in range(3):
            # 0x7 is code for setting all three RWCs for that thread
            self.tensix_debug.inject_instruction(
                ops.TT_OP_SETRWC(0, 0, rwc_dst[thread_id], rwc_b[thread_id], rwc_a[thread_id], 0x7), thread_id
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
        ops = self.location.device.instructions

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
            op = ops.TT_OP_SETDVALID(operand) if instruction == "SETDVALID" else ops.TT_OP_CLEARDVALID(operand, 0)
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
