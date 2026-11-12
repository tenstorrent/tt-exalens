# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import math
import struct
import unittest
from parameterized import parameterized_class, parameterized
import tt_umd
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
        self.tensix_debug = TensixDebug(self.location, self.neo_id)
        debug_bus = self.location.noc_block.get_debug_bus(self.neo_id)
        assert debug_bus is not None
        self.debug_bus = debug_bus

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
        if not self.is_blackhole():
            self.skipTest("Direct read/write of 8-bit integers is supported only on Blackhole.")

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
            self.skipTest("Direct read/write of 8-bit integers is supported only on Blackhole.")

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

    def test_read_regfile_16bit(self):
        if self.tensix_debug.dest is None or not self.location.device.is_quasar():
            self.skipTest("Reading 16-bit dest directly is supported only on Quasar.")

        def float16_b_bits(value: float) -> int:
            return int.from_bytes(struct.pack(">f", value), byteorder="big") >> 16

        upper = [float(i % 256 - 128) for i in range(TILE_SIZE)]
        lower = [(i % 64) / 64 for i in range(TILE_SIZE)]
        # A Float32 in dest keeps its upper 16 bits in 16-bit row r and its lower 16 bits in row r + 256.
        # Dest stores Float16_b as sign, mantissa, exponent, so the lower half is written in that order.
        data = []
        for upper_value, lower_value in zip(upper, lower):
            bits = float16_b_bits(lower_value)
            stored = (bits & 0x8000) | ((bits & 0x7F) << 8) | ((bits >> 7) & 0xFF)
            word = (float16_b_bits(upper_value) << 16) | stored
            data.append(struct.unpack(">f", word.to_bytes(4, byteorder="big"))[0])
        self.tensix_debug.write_regfile(REGFILE.DSTACC, data, TensixDataFormat.Float32)
        self.tensix_debug.register_store.write_register("ALU_ACC_CTRL_Fp32_enabled", 0)
        self.tensix_debug.register_store.write_register(
            "ALU_FORMAT_SPEC_REG_SrcA_val", TensixDataFormat.Float16_b.value
        )

        values = self.tensix_debug.read_regfile(REGFILE.DSTACC, 5)
        self.assertEqual(values[:TILE_SIZE], upper)
        self.assertEqual(values[4 * TILE_SIZE : 5 * TILE_SIZE], lower)

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
