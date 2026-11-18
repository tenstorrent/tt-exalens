# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import math
import unittest
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

        def give_back():
            self.tensix_debug.inject_instruction(self.ops.TT_OP_CLEARDVALID(operand, 0), 0)

        def give_back_all():
            for _ in range(2):
                if read(bank_mxu_allowed[0]) or read(bank_mxu_allowed[1]):
                    give_back()

        # SETDVALID waits while the matrix unit holds the unpacker's bank, so start with both banks given back,
        # and leave no bank with the matrix unit if a check fails.
        give_back_all()
        self.addCleanup(give_back_all)

        unpacker = read(unpacker_bank)
        mxu = read(mxu_bank)
        allowed = [0, 0]

        def check(step: str):
            expected = {
                unpacker_bank: unpacker,
                mxu_bank: mxu,
                bank_mxu_allowed[0]: allowed[0],
                bank_mxu_allowed[1]: allowed[1],
                mxu_allowed: allowed[mxu],
                unpacker_allowed: 1 - allowed[unpacker],
            }
            actual = {signal_name: read(signal_name) for signal_name in expected}
            self.assertEqual(actual, expected, f"after {step}")

        check("giving back both banks")
        # Two rounds, so that each bank is given and given back once.
        for round_id in range(2):
            self.tensix_debug.inject_instruction(self.ops.TT_OP_SETDVALID(operand), 0)
            allowed[unpacker] = 1
            unpacker ^= 1
            check(f"SETDVALID, round {round_id}")

            give_back()
            allowed[mxu] = 0
            mxu ^= 1
            check(f"CLEARDVALID, round {round_id}")
