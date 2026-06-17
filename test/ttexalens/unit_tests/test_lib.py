# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import unittest
import os
import struct

import itertools
from functools import wraps
from datetime import timedelta

from parameterized import parameterized, parameterized_class

from test.ttexalens.unit_tests.test_base import get_core_location, get_parsed_elf_file, init_cached_test_context
import ttexalens as lib
from ttexalens import util
from ttexalens.exceptions import TTException
from ttexalens.elf import ElfFile
from ttexalens.memory_map import MemoryMap, MemoryMapBlockInfo

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.device import Device, UnsafeAccessException
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription
from ttexalens.memory_access import create_l1_memory_access, create_memory_access
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.elf import CallstackEntry, CallstackEntryVariable
from ttexalens.hardware.risc_debug import RiscDebug

from ttexalens.register_store import ConfigurationRegisterDescription, DebugRegisterDescription
from ttexalens.elf_loader import ElfLoader
from ttexalens.hardware.arc_block import CUTOFF_FIRMWARE_VERSION

from ttexalens.gdb.gdb_client import get_gdb_callstack
from ttexalens.gdb.gdb_communication import ServerSocket
from ttexalens.gdb.gdb_server import GdbServer


def _read_bytes(rd: RiscDebug, address: int, size_bytes: int, safe_mode: bool | None = None) -> bytes:
    """Test helper: allocate a buffer, fill it via the buffer-based read_memory_bytes, and return bytes."""
    buffer = bytearray(size_bytes)
    rd.read_memory_bytes(address, buffer, safe_mode=safe_mode)
    return bytes(buffer)


def invalid_argument_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        return func(*args, **kwargs)

    return wrapper


class TestAutoContext(unittest.TestCase):
    def test_auto_context(self):
        """Test auto context creation."""
        lib.set_active_context(None)
        context = lib.check_context()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

    def test_set_global_context(self):
        """Test setting global context."""
        import ttexalens.tt_exalens_init as init

        lib.set_active_context(None)
        context = lib.init_ttexalens()
        self.assertIsNotNone(init.GLOBAL_CONTEXT)
        self.assertIs(init.GLOBAL_CONTEXT, context)

    def test_existing_context(self):
        """Test recognition of existing context."""
        import ttexalens.tt_exalens_init as init

        lib.set_active_context(None)

        # Create new global context
        context1 = lib.init_ttexalens()
        self.assertIsNotNone(init.GLOBAL_CONTEXT)
        self.assertIs(init.GLOBAL_CONTEXT, context1)

        # Check for existing context
        context = lib.check_context()
        self.assertIsNotNone(context)
        self.assertIs(init.GLOBAL_CONTEXT, context)
        self.assertIs(context, context1)


class TestReadWrite(unittest.TestCase):
    context: Context

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()

    def setUp(self):
        self.assertIsNotNone(self.context)
        self.assertIsInstance(self.context, Context)

    def test_write_read(self):
        """Test write data -- read data."""
        location = "0,0"
        address = 0x100

        data = [0, 1, 2, 3]

        lib.write_to_device(location, address, data)
        ret = lib.read_from_device(location, address, num_bytes=len(data))
        self.assertEqual(ret, bytes(data))

    def test_write_read_bytes(self):
        """Test write bytes -- read bytes."""
        location = "1,0"
        address = 0x100

        data = b"abcd"

        lib.write_to_device(location, address, data)
        ret = lib.read_from_device(location, address, num_bytes=len(data))
        self.assertEqual(ret, data)

    def test_write_read_data_integrity(self):
        location = "0,0"
        num_of_words = 256  # 1024 bytes
        pattern_words = 50  # 200 bytes
        offset = 16
        data = [0x12345678] * num_of_words  # Initial pattern to write
        lib.write_words_to_device(location, 0, data)
        self.assertEqual(lib.read_words_from_device(location, 0, word_count=num_of_words), data)
        lib.write_words_to_device(
            location, offset, [0xDEADBEEF] * pattern_words
        )  # Overwrite part of the initial pattern
        data[offset // 4 : offset // 4 + pattern_words] = [0xDEADBEEF] * pattern_words
        self.assertEqual(lib.read_words_from_device(location, 0, word_count=num_of_words), data)

    def test_write_read_bytes_over_dma(self):
        """Test write bytes -- read bytes."""
        location_str = "1,0"
        location = OnChipCoordinate.create(location_str, self.context.devices[0])
        data = b"test_me!" * 16  # 128 bytes
        read_data = bytearray(len(data))
        for address in range(0, 128, 1):
            # Write over regular TLB access to clean any previous data
            location.noc_write(address, b"\x00" * len(data), use_4B_mode=False, dma_threshold=len(data) + 1)

            # Write over DMA
            location.noc_write(address, data, use_4B_mode=False, dma_threshold=0)

            # Read over regular TLB access
            location.noc_read(address, read_data, use_4B_mode=False, dma_threshold=len(data) + 1)
            self.assertEqual(read_data, data)

            # Read over DMA
            location.noc_read(address, read_data, use_4B_mode=False, dma_threshold=0)
            self.assertEqual(read_data, data)

    @parameterized.expand(
        [
            ("1,0", 1024, 0x100, 0),  # 1KB from device 0 at location 1,0
            ("1,0", 2048, 0x104, 0),  # 2KB from device 0 at location 1,0
            ("1,0", 4096, 0x108, 0),  # 4KB from device 0 at location 1,0
            ("1,0", 8192, 0x10C, 0),  # 8KB from device 0 at location 1,0
            ("1,0", 1024, 0x100, 1),  # 1KB from device 1 at location 1,0
            ("1,0", 2048, 0x104, 1),  # 2KB from device 1 at location 1,0
            ("1,0", 4096, 0x108, 1),  # 4KB from device 1 at location 1,0
            ("1,0", 8192, 0x10C, 1),  # 8KB from device 1 at location 1,0
            ("ch0", 1024, 0x100, 0),  # 1KB from device 0 at location DRAM channel 0
            ("ch0", 2048, 0x104, 0),  # 2KB from device 0 at location DRAM channel 0
            ("ch0", 4096, 0x108, 0),  # 4KB from device 0 at location DRAM channel 0
            ("ch0", 8192, 0x10C, 0),  # 8KB from device 0 at location DRAM channel 0
            ("ch0", 1024, 0x100, 1),  # 1KB from device 1 at location DRAM channel 0
            ("ch0", 2048, 0x104, 1),  # 2KB from device 1 at location DRAM channel 0
            ("ch0", 4096, 0x108, 1),  # 4KB from device 1 at location DRAM channel 0
            ("ch0", 8192, 0x10C, 1),  # 8KB from device 1 at location DRAM channel 0
        ]
    )
    def test_write_read_bytes_buffer(self, location: str, size: int, address: int, device_id: int):
        """Test write bytes -- read bytes but with bigger buffer."""

        if device_id not in self.context.devices:
            self.skipTest("Device ID not available.")

        # Create buffer
        data = bytes([i % 256 for i in range(size)])
        words = [int.from_bytes(data[i : i + 4], byteorder="little") for i in range(0, len(data), 4)]

        # Write buffer
        lib.write_to_device(location, address, data, device_id)

        # Verify buffer as words
        read_words = lib.read_words_from_device(location, address, device_id, len(words))
        self.assertEqual(read_words, words)

        # Write words
        lib.write_words_to_device(location, address, words, device_id)

        # Read buffer
        read_bytes = lib.read_from_device(location, address, device_id, num_bytes=len(data))
        self.assertEqual(read_bytes, data)

    def test_write_read_words(self):
        """Test write words -- read words."""
        location = "1,0"

        address = [0x100, 0x104, 0x108]
        data = [156, 2, 212, 9]

        # Write a word to device two times
        ret = lib.write_words_to_device(location, address[0], data[0])

        ret = lib.write_words_to_device(location, address[1], data[1])

        # Write two words to device
        ret = lib.write_words_to_device(location, address[2], data[2:])

        # Read the first word
        ret = lib.read_words_from_device(location, address[0])
        self.assertEqual(ret[0], data[0])

        # Read the second word
        ret = lib.read_words_from_device(location, address[1])
        self.assertEqual(ret[0], data[1])

        # Read first two words
        ret = lib.read_words_from_device(location, address[0], word_count=2)
        self.assertEqual(ret, data[0:2])

        # Read third and fourth words
        ret = lib.read_words_from_device(location, address[2], word_count=2)
        self.assertEqual(ret, data[2:])

    def test_write_bytes_read_words(self):
        """Test write bytes -- read words."""
        location = "1,0"
        address = 0x100
        data = [0, 1, 2, 3]

        # Write bytes to device
        lib.write_to_device(location, address, data)

        # Read the bytes as words
        ret = lib.read_words_from_device(location, address, word_count=1)
        self.assertEqual(ret[0].to_bytes(4, "little"), bytes(data))

    @parameterized.expand(
        [
            ("abcd", 0x100, 0, 1),  # Invalid location string
            ("-10", 0x100, 0, 1),  # Invalid location string
            ("0,0", -1, 0, 1),  # Invalid address
            ("0,0", 0x100, -1, 1),  # Invalid device_id
            ("0,0", 0x100, 112, 1),  # Invalid device_id (too high)
            ("0,0", 0x100, 0, -1),  # Invalid word_count
            ("0,0", 0x100, 0, 0),  # Invalid word_count
        ]
    )
    def test_invalid_inputs_read(self, location, address, device_id, word_count):
        """Test invalid inputs for read functions."""
        with self.assertRaises((TTException, ValueError)):
            lib.read_words_from_device(location, address, device_id, word_count)
        with self.assertRaises((TTException, ValueError)):
            # word_count can be used as num_bytes
            lib.read_from_device(location, address, device_id, word_count)

    @parameterized.expand(
        [
            ("abcd", 0x100, 5, 0),  # Invalid location string
            ("-10", 0x100, 5, 0),  # Invalid location string
            ("0,0", -1, 5, 0),  # Invalid address
            ("0,0", 0x100, 5, -1),  # Invalid device_id
            ("0,0", 0x100, 5, 112),  # Invalid device_id (too high)
            # ("0,0", 0x100, -171, -1),        # Invalid word TODO: What are the limits for word?
        ]
    )
    def test_invalid_write_word(self, location, address, data, device_id):
        with self.assertRaises((TTException, ValueError)):
            lib.write_words_to_device(location, address, data, device_id)

    @parameterized.expand(
        [
            ("abcd", 0x100, b"abcd", 0),  # Invalid location string
            ("-10", 0x100, b"abcd", 0),  # Invalid location string
            ("0,0", -1, b"abcd", 0),  # Invalid address
            ("0,0", 0x100, b"abcd", -1),  # Invalid device_id
            ("0,0", 0x100, b"abcd", 112),  # Invalid device_id (too high)
            ("0,0", 0x100, [], 0),  # Invalid data
            ("0,0", 0x100, b"", 0),  # Invalid data
        ]
    )
    def test_invalid_write(self, location, address, data, device_id):
        """Test invalid inputs for write function."""
        with self.assertRaises((TTException, ValueError)):
            lib.write_to_device(location, address, data, device_id)

    def test_unaligned_read(self):
        for device_id in self.context.device_ids:
            location = self.context.devices[device_id].get_block_locations()[0]
            lib.write_words_to_device(location, 0, [0x12345678, 0x90ABCDEF], device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x12345678, 0x90ABCDEF]
            assert lib.read_from_device(location, 0, device_id, 1, self.context) == bytes([0x78])
            assert lib.read_from_device(location, 1, device_id, 1, self.context) == bytes([0x56])
            assert lib.read_from_device(location, 2, device_id, 1, self.context) == bytes([0x34])
            assert lib.read_from_device(location, 3, device_id, 1, self.context) == bytes([0x12])
            assert lib.read_from_device(location, 4, device_id, 1, self.context) == bytes([0xEF])
            assert lib.read_from_device(location, 5, device_id, 1, self.context) == bytes([0xCD])
            assert lib.read_from_device(location, 6, device_id, 1, self.context) == bytes([0xAB])
            assert lib.read_from_device(location, 7, device_id, 1, self.context) == bytes([0x90])
            assert lib.read_from_device(location, 0, device_id, 2, self.context) == bytes([0x78, 0x56])
            assert lib.read_from_device(location, 2, device_id, 2, self.context) == bytes([0x34, 0x12])
            assert lib.read_from_device(location, 4, device_id, 2, self.context) == bytes([0xEF, 0xCD])
            assert lib.read_from_device(location, 6, device_id, 2, self.context) == bytes([0xAB, 0x90])
            assert lib.read_from_device(location, 0, device_id, 4, self.context) == bytes([0x78, 0x56, 0x34, 0x12])
            assert lib.read_from_device(location, 4, device_id, 4, self.context) == bytes([0xEF, 0xCD, 0xAB, 0x90])
            assert lib.read_from_device(location, 0, device_id, 8, self.context) == bytes(
                [0x78, 0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB, 0x90]
            )
            assert lib.read_from_device(location, 1, device_id, 2, self.context) == bytes([0x56, 0x34])
            assert lib.read_from_device(location, 3, device_id, 2, self.context) == bytes([0x12, 0xEF])
            assert lib.read_from_device(location, 5, device_id, 2, self.context) == bytes([0xCD, 0xAB])
            assert lib.read_from_device(location, 1, device_id, 4, self.context) == bytes([0x56, 0x34, 0x12, 0xEF])
            assert lib.read_from_device(location, 2, device_id, 4, self.context) == bytes([0x34, 0x12, 0xEF, 0xCD])
            assert lib.read_from_device(location, 3, device_id, 4, self.context) == bytes([0x12, 0xEF, 0xCD, 0xAB])
            assert lib.read_from_device(location, 0, device_id, 8, self.context) == bytes(
                [0x78, 0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB, 0x90]
            )
            assert lib.read_from_device(location, 1, device_id, 6, self.context) == bytes(
                [0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB]
            )

    def test_unaligned_write(self):
        for device_id in self.context.device_ids:
            location = self.context.devices[device_id].get_block_locations()[0]
            lib.write_words_to_device(location, 0, [0xDEADBEEF, 0xDEADBEEF], device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0xDEADBEEF, 0xDEADBEEF]
            lib.write_to_device(location, 0, bytes([0x12]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0xDEADBE12, 0xDEADBEEF]
            lib.write_to_device(location, 1, bytes([0x34]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0xDEAD3412, 0xDEADBEEF]
            lib.write_to_device(location, 2, bytes([0x56]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0xDE563412, 0xDEADBEEF]
            lib.write_to_device(location, 3, bytes([0x78]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x78563412, 0xDEADBEEF]
            lib.write_to_device(location, 4, bytes([0x90]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x78563412, 0xDEADBE90]
            lib.write_to_device(location, 5, bytes([0xAB]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x78563412, 0xDEADAB90]
            lib.write_to_device(location, 6, bytes([0xCD]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x78563412, 0xDECDAB90]
            lib.write_to_device(location, 7, bytes([0xEF]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x78563412, 0xEFCDAB90]
            lib.write_to_device(location, 0, bytes([0xAA, 0xBB]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x7856BBAA, 0xEFCDAB90]
            lib.write_to_device(location, 2, bytes([0xCC, 0xDD]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0xDDCCBBAA, 0xEFCDAB90]
            lib.write_to_device(location, 4, bytes([0xEE, 0xFF]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0xDDCCBBAA, 0xEFCDFFEE]
            lib.write_to_device(location, 6, bytes([0x00, 0x11]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0xDDCCBBAA, 0x1100FFEE]
            lib.write_to_device(location, 1, bytes([0x22, 0x33]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0xDD3322AA, 0x1100FFEE]
            lib.write_to_device(location, 3, bytes([0x44, 0x55]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x443322AA, 0x1100FF55]
            lib.write_to_device(location, 5, bytes([0x66, 0x77]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x443322AA, 0x11776655]
            lib.write_to_device(location, 2, bytes([0x88, 0x99, 0xAA]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x998822AA, 0x117766AA]
            lib.write_to_device(location, 3, bytes([0xBB, 0xCC, 0xDD]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0xBB8822AA, 0x1177DDCC]
            lib.write_to_device(location, 1, bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66]), device_id, self.context)
            assert lib.read_words_from_device(location, 0, device_id, 2, self.context) == [0x332211AA, 0x11665544]

    @parameterized.expand(
        [
            (
                "0,0",
                ConfigurationRegisterDescription(index=1, mask=0x1E000000, shift=25),
                2,
            ),  # ALU_FORMAT_SPEC_REG2_Dstacc
            ("0,0", DebugRegisterDescription(offset=0x54), 18),  # RISCV_DEBUG_REG_DBG_BUS_CNTL_REG
            ("0,0", "UNPACK_CONFIG0_out_data_format", 6),
            ("0,0", "RISCV_DEBUG_REG_DBG_ARRAY_RD_EN", 1),
            ("0,0", "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0", 9),
            ("0,0", "OPERAND_BASE_ADDR_T0", 4),
            ("0,0", "PERF_EPOCH_BASE_ADDR_T1", 8),
            ("0,0", "OUTPUT_ADDR_T2", 12),
        ]
    )
    def test_write_read_tensix_register(self, location, register, value):
        """Test writing and reading tensix registers"""

        # Storing the original value of the register
        original_value = lib.read_register(location, register)

        # Writing a value to the register and reading it back
        lib.write_register(location, register, value)
        ret = lib.read_register(location, register)

        # Checking if the value was written and read correctly
        self.assertEqual(ret, value)

        # Writing the original value back to the register and reading it
        lib.write_register(location, register, original_value)
        ret = lib.read_register(location, register)

        # Checking if read value is equal to the original value
        self.assertEqual(ret, original_value)

    @parameterized.expand(
        [
            (
                "0,0",
                ConfigurationRegisterDescription(index=1, mask=0x1E000000, shift=25),
                "ALU_FORMAT_SPEC_REG2_Dstacc",
            ),
            ("0,0", DebugRegisterDescription(offset=0x54), "RISCV_DEBUG_REG_DBG_BUS_CNTL_REG"),
            ("0,0", DebugRegisterDescription(offset=0x60), "RISCV_DEBUG_REG_DBG_ARRAY_RD_EN"),
            ("0,0", DebugRegisterDescription(offset=0xA0), "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0"),
        ]
    )
    def test_write_read_tensix_register_with_name(self, location, register_description, register_name):
        "Test writing and reading tensix registers with name"

        # Reading original values of registers
        original_val_desc = lib.read_register(location, register_description)
        original_val_name = lib.read_register(location, register_name)

        # Checking if values are equal
        self.assertEqual(original_val_desc, original_val_name)

        # Writing a value to the register given by description
        lib.write_register(location, register_description, 1)

        # Reading values from both registers
        val_desc = lib.read_register(location, register_description)
        val_name = lib.read_register(location, register_name)

        # Checking if writing to description register affects the name register (making sure they are the same)
        self.assertEqual(val_desc, val_name)

        # Wrting original value back
        lib.write_register(location, register_name, original_val_name)

        val_desc = lib.read_register(location, register_description)
        val_name = lib.read_register(location, register_name)

        # Checking if original values are restored
        self.assertEqual(val_name, original_val_name)
        self.assertEqual(val_desc, original_val_desc)

    @parameterized.expand(
        [
            ("abcd", ConfigurationRegisterDescription(), 0, 0),  # Invalid location string
            ("-10", ConfigurationRegisterDescription(), 0, 0),  # Invalid location string
            ("0,0", ConfigurationRegisterDescription(), 0, -1),  # Invalid device_id
            ("0,0", ConfigurationRegisterDescription(), 0, 112),  # Invalid device_id (too high)
            ("0,0", DebugBusSignalDescription(), 0, 0),  # Invalid register type
            ("0,0", "invalid_register_name", 0, 0),  # Invalid register name
            ("0,0", ConfigurationRegisterDescription(), 0, -1),  # Invalid value (negative)
            ("0,0", "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0", 0, 2**32),  # Invalid value (too high)
            ("0,0", ConfigurationRegisterDescription(index=-1), 0, 0),  # Invalid index (negative)
            ("0,0", ConfigurationRegisterDescription(index=2**14), 0, 0),  # Invalid index (too high)
            ("0,0", 0xFFB12345, 0, 0),  # Address alone is not enough to represent index)
            ("0,0", ConfigurationRegisterDescription(mask=-1), 0, 0),  # Invalid mask (negative)
            ("0,0", ConfigurationRegisterDescription(mask=2**32), 0, 0),  # Invalid mask (too high)
            ("0,0", ConfigurationRegisterDescription(shift=-1), 0, 0),  # Invalid shift (negative)
            ("0,0", ConfigurationRegisterDescription(shift=32), 0, 0),  # Invalid shift (too high)
        ]
    )
    def test_invalid_write_read_tensix_register(self, location, register, value, device_id):
        """Test invalid inputs for tensix register read and write functions."""

        if value == 0:  # Invalid value does not raies an exception in read so we skip it
            with self.assertRaises((TTException, ValueError)):
                lib.read_register(location, register, device_id)
        with self.assertRaises((TTException, ValueError)):
            lib.write_register(location, register, value, device_id)

    @parameterized.expand(
        [
            ("0,0",),
            ("1,1",),
            ("2,2",),
        ]
    )
    def test_read_write_cfg_register(self, location):
        """Test reading and writing configuration registers using lib functions."""

        cfg_reg_name = "ALU_FORMAT_SPEC_REG2_Dstacc"

        # Store original value
        original_value = lib.read_register(location, cfg_reg_name)

        # Test writing and reading different values
        lib.write_register(location, cfg_reg_name, 10)
        assert lib.read_register(location, cfg_reg_name) == 10

        lib.write_register(location, cfg_reg_name, 0)
        assert lib.read_register(location, cfg_reg_name) == 0

        lib.write_register(location, cfg_reg_name, 5)
        assert lib.read_register(location, cfg_reg_name) == 5

        # Restore original value
        lib.write_register(location, cfg_reg_name, original_value)

    @parameterized.expand(
        [
            ("0,0",),
            ("1,1",),
            ("2,2",),
        ]
    )
    def test_read_write_dbg_register(self, location):
        """Test reading and writing debug registers using lib functions."""

        dbg_reg_name = "RISCV_DEBUG_REG_CFGREG_RD_CNTL"

        # Store original value
        original_value = lib.read_register(location, dbg_reg_name)

        # Test writing and reading different values
        lib.write_register(location, dbg_reg_name, 10)
        assert lib.read_register(location, dbg_reg_name) == 10

        lib.write_register(location, dbg_reg_name, 0)
        assert lib.read_register(location, dbg_reg_name) == 0

        lib.write_register(location, dbg_reg_name, 5)
        assert lib.read_register(location, dbg_reg_name) == 5

        # Restore original value
        lib.write_register(location, dbg_reg_name, original_value)

    @parameterized.expand(
        [
            ("0,0", 1),
            ("1,1", 1),
            ("0,0", -1),
            ("1,1", -1),
        ]
    )
    def test_cfg_register_index_out_of_bounds(self, location, delta):
        """Test that reading/writing a configuration register with index beyond valid range raises ValueError."""

        loc = OnChipCoordinate.create(location, device=self.context.devices[0])
        register_store = self.context.devices[0].get_block(loc).get_register_store()

        # Get the maximum valid config register index
        max_index = register_store._max_config_register_index

        # Create a ConfigurationRegisterDescription with an invalid index (too high)
        index = max_index + delta if delta > 0 else delta
        invalid_cfg_reg = ConfigurationRegisterDescription(index=index)

        # Test that reading raises ValueError
        with self.assertRaises(ValueError):
            lib.read_register(location, invalid_cfg_reg)

        # Test that writing raises ValueError
        with self.assertRaises(ValueError):
            lib.write_register(location, invalid_cfg_reg, 0)

    @parameterized.expand(
        [
            ("0,0", "brisc"),
            ("1,0", "brisc"),
            ("1,0", "brisc"),
            ("1,0", "trisc0"),
            ("0,1", "brisc"),
            ("1,1", "brisc"),
            ("0,0", "brisc"),  # noc_id = 1
            ("0,0", "trisc0"),
            ("0,0", "trisc1"),
            ("0,0", "trisc2"),
            ("0,0", "trisc0", -4),  # last address for trisc for wormhole
            ("0,0", "brisc", -4),  # last address for brisc for wormhole
            # Testing unaligned read/write
            ("0,0", "brisc", 1),
            ("0,0", "trisc0", 2),
            ("0,0", "trisc1", 3),
            ("0,0", "trisc2", 1),
            ("1,0", "brisc", -5),
        ]
    )
    def test_write_read_private_memory(self, location: str, risc_name: str, offset: int = 0):
        """Testing read_memory and write_memory through debugging interface on private core memory range."""

        loc = OnChipCoordinate.create(location, device=self.context.devices[0])
        risc_debug = loc._device.get_block(loc).get_risc_debug(risc_name)

        private_memory = risc_debug.get_data_private_memory()
        assert private_memory is not None, "Private memory is not available."
        assert private_memory.address.private_address is not None, "Private memory address is not set."
        addr = (
            private_memory.address.private_address + offset
            if offset >= 0
            else private_memory.address.private_address + private_memory.size + offset
        )

        with risc_debug.ensure_private_memory_access():
            self.assertFalse(risc_debug.is_in_reset())

            original_value = lib.read_riscv_memory(loc, addr, risc_name)

            # Writing a value to the memory and reading it back
            value = 0x12345678
            lib.write_riscv_memory(loc, addr, value, risc_name)
            ret = lib.read_riscv_memory(loc, addr, risc_name)
            self.assertEqual(ret, value)
            # Writing the original value back to the memory
            lib.write_riscv_memory(loc, addr, original_value, risc_name)
            ret = lib.read_riscv_memory(loc, addr, risc_name)
            self.assertEqual(ret, original_value)

    @parameterized.expand(
        [
            ("abcd", 0xFFB00000, 0),  # Invalid location string
            ("-10", 0xFFB00000, 0),  # Invalid location string
            ("0,0", 0xFFA00000, 0),  # Invalid address (too low)
            ("0,0", 0xFFC00000, 0),  # Invalid address (too high)
            ("0,0", 0xFFB00000, 0, "invalid"),  # Invalid risc_name
            ("0,0", 0xFFB00000, 0, "brisc", -1),  # Invalid device_id
            ("0,0", 0xFFB00000, 0, "brisc", 2**32),  # Invalid device_id
        ]
    )
    def test_invalid_read_private_memory(self, location: str, address: int, value: int, risc_name="brisc", device_id=0):
        """Test invalid inputs for reading private memory."""
        if value == 0:  # Invalid value does not raies an exception in read so we skip it
            with self.assertRaises((TTException, ValueError)):
                lib.read_riscv_memory(location, address, risc_name, None, device_id)
        with self.assertRaises((TTException, ValueError)):
            lib.write_riscv_memory(location, address, value, risc_name, None, device_id)

    @parameterized.expand(
        [
            ("0,0", "brisc"),
            ("0,0", "trisc0"),
            ("0,0", "trisc1"),
            ("0,0", "trisc2"),
            ("1,0", "brisc"),
            ("1,0", "trisc0"),
            ("1,0", "trisc1"),
            ("1,0", "trisc2"),
        ]
    )
    def test_unaligned_read_private_memory(self, loc_str: str, risc_name: str):
        device = self.context.devices[0]
        if device.is_blackhole() and risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        location = OnChipCoordinate.create(loc_str, device)
        risc_debug = location._device.get_block(location).get_risc_debug(risc_name)
        with risc_debug.ensure_private_memory_access():
            private_memory = risc_debug.get_data_private_memory()
            assert private_memory is not None, "Private memory is not available."
            assert private_memory.address.private_address is not None, "Private memory address is not set."
            address = private_memory.address.private_address
            risc_debug.write_memory_bytes(address, bytes([0x78, 0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB, 0x90]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0x78, 0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB, 0x90])
            )
            self.assertEqual(_read_bytes(risc_debug, address + 0, 1), bytes([0x78]))
            self.assertEqual(_read_bytes(risc_debug, address + 1, 1), bytes([0x56]))
            self.assertEqual(_read_bytes(risc_debug, address + 2, 1), bytes([0x34]))
            self.assertEqual(_read_bytes(risc_debug, address + 3, 1), bytes([0x12]))
            self.assertEqual(_read_bytes(risc_debug, address + 4, 1), bytes([0xEF]))
            self.assertEqual(_read_bytes(risc_debug, address + 5, 1), bytes([0xCD]))
            self.assertEqual(_read_bytes(risc_debug, address + 6, 1), bytes([0xAB]))
            self.assertEqual(_read_bytes(risc_debug, address + 7, 1), bytes([0x90]))
            self.assertEqual(_read_bytes(risc_debug, address + 0, 2), bytes([0x78, 0x56]))
            self.assertEqual(_read_bytes(risc_debug, address + 2, 2), bytes([0x34, 0x12]))
            self.assertEqual(_read_bytes(risc_debug, address + 4, 2), bytes([0xEF, 0xCD]))
            self.assertEqual(_read_bytes(risc_debug, address + 6, 2), bytes([0xAB, 0x90]))
            self.assertEqual(_read_bytes(risc_debug, address + 0, 4), bytes([0x78, 0x56, 0x34, 0x12]))
            self.assertEqual(_read_bytes(risc_debug, address + 4, 4), bytes([0xEF, 0xCD, 0xAB, 0x90]))
            self.assertEqual(
                _read_bytes(risc_debug, address + 0, 8), bytes([0x78, 0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB, 0x90])
            )
            self.assertEqual(_read_bytes(risc_debug, address + 1, 2), bytes([0x56, 0x34]))
            self.assertEqual(_read_bytes(risc_debug, address + 3, 2), bytes([0x12, 0xEF]))
            self.assertEqual(_read_bytes(risc_debug, address + 5, 2), bytes([0xCD, 0xAB]))
            self.assertEqual(_read_bytes(risc_debug, address + 1, 4), bytes([0x56, 0x34, 0x12, 0xEF]))
            self.assertEqual(_read_bytes(risc_debug, address + 2, 4), bytes([0x34, 0x12, 0xEF, 0xCD]))
            self.assertEqual(_read_bytes(risc_debug, address + 3, 4), bytes([0x12, 0xEF, 0xCD, 0xAB]))
            self.assertEqual(
                _read_bytes(risc_debug, address + 0, 8), bytes([0x78, 0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB, 0x90])
            )
            self.assertEqual(_read_bytes(risc_debug, address + 1, 6), bytes([0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB]))

    @parameterized.expand(
        [
            ("0,0", "brisc"),
            ("0,0", "trisc0"),
            ("0,0", "trisc1"),
            ("0,0", "trisc2"),
            ("1,0", "brisc"),
            ("1,0", "trisc0"),
            ("1,0", "trisc1"),
            ("1,0", "trisc2"),
        ]
    )
    def test_unaligned_write_private_memory(self, loc_str: str, risc_name: str):
        device = self.context.devices[0]
        if device.is_blackhole() and risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        location = OnChipCoordinate.create(loc_str, device)
        risc_debug = location._device.get_block(location).get_risc_debug(risc_name)
        with risc_debug.ensure_private_memory_access():
            private_memory = risc_debug.get_data_private_memory()
            assert private_memory is not None, "Private memory is not available."
            assert private_memory.address.private_address is not None, "Private memory address is not set."
            address = private_memory.address.private_address
            risc_debug.write_memory_bytes(address, bytes([0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xDE, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF])
            )
            risc_debug.write_memory_bytes(address + 0, bytes([0x12]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0x12, 0xAD, 0xBE, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF])
            )
            risc_debug.write_memory_bytes(address + 1, bytes([0x34]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0x12, 0x34, 0xBE, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF])
            )
            risc_debug.write_memory_bytes(address + 2, bytes([0x56]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0x12, 0x34, 0x56, 0xEF, 0xDE, 0xAD, 0xBE, 0xEF])
            )
            risc_debug.write_memory_bytes(address + 3, bytes([0x78]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0x12, 0x34, 0x56, 0x78, 0xDE, 0xAD, 0xBE, 0xEF])
            )
            risc_debug.write_memory_bytes(address + 4, bytes([0x90]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0x12, 0x34, 0x56, 0x78, 0x90, 0xAD, 0xBE, 0xEF])
            )
            risc_debug.write_memory_bytes(address + 5, bytes([0xAB]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0x12, 0x34, 0x56, 0x78, 0x90, 0xAB, 0xBE, 0xEF])
            )
            risc_debug.write_memory_bytes(address + 6, bytes([0xCD]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0x12, 0x34, 0x56, 0x78, 0x90, 0xAB, 0xCD, 0xEF])
            )
            risc_debug.write_memory_bytes(address + 7, bytes([0xFE]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0x12, 0x34, 0x56, 0x78, 0x90, 0xAB, 0xCD, 0xFE])
            )
            risc_debug.write_memory_bytes(address + 0, bytes([0xAA, 0xBB]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xAA, 0xBB, 0x56, 0x78, 0x90, 0xAB, 0xCD, 0xFE])
            )
            risc_debug.write_memory_bytes(address + 2, bytes([0xCC, 0xDD]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xAA, 0xBB, 0xCC, 0xDD, 0x90, 0xAB, 0xCD, 0xFE])
            )
            risc_debug.write_memory_bytes(address + 4, bytes([0xEE, 0xFF]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0xCD, 0xFE])
            )
            risc_debug.write_memory_bytes(address + 6, bytes([0x00, 0x11]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00, 0x11])
            )
            risc_debug.write_memory_bytes(address + 1, bytes([0x22, 0x33]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xAA, 0x22, 0x33, 0xDD, 0xEE, 0xFF, 0x00, 0x11])
            )
            risc_debug.write_memory_bytes(address + 3, bytes([0x44, 0x55]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xAA, 0x22, 0x33, 0x44, 0x55, 0xFF, 0x00, 0x11])
            )
            risc_debug.write_memory_bytes(address + 5, bytes([0x66, 0x77]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xAA, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x11])
            )
            risc_debug.write_memory_bytes(address + 2, bytes([0x88, 0x99, 0xAA]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xAA, 0x22, 0x88, 0x99, 0xAA, 0x66, 0x77, 0x11])
            )
            risc_debug.write_memory_bytes(address + 3, bytes([0xBB, 0xCC, 0xDD]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xAA, 0x22, 0x88, 0xBB, 0xCC, 0xDD, 0x77, 0x11])
            )
            risc_debug.write_memory_bytes(address + 1, bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66]))
            self.assertEqual(
                _read_bytes(risc_debug, address, 8), bytes([0xAA, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x11])
            )


class TestSafeAccess(unittest.TestCase):
    context: Context

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()

    @classmethod
    def tearDownClass(cls):
        cls.context.safe_mode = False  # Reset safe mode for any subsequent tests that use the context

    def setUp(self):
        self.assertIsNotNone(self.context)
        self.assertIsInstance(self.context, Context)
        self.context.safe_mode = True

    def test_comprehensive_block_access(self):
        """Comprehensive test that validates safe access patterns for all blocks on all devices.

        This test:
        1. Iterates through all devices and all block types
        2. Tests read/write access fully inside each block based on safety flags
        3. Tests access spanning into adjacent readable blocks
        4. Tests access spanning into unreadable/unmapped regions (should fail)
        """

        # Get all block types
        all_block_types = [
            "functional_workers",
            "dram",
            "eth",
        ]

        for device_id, device in self.context.devices.items():
            # Collect test locations from all block types
            test_locations = []
            for block_type in all_block_types:
                locations = device.get_block_locations(block_type=block_type)
                # Take up to 2 locations per block type to keep test time reasonable
                if len(locations) > 0:
                    test_locations.extend(locations[:2] if len(locations) >= 2 else locations)

            for location in test_locations:
                block = device.get_block(location)
                memory_map = block.noc_memory_map

                if device.is_wormhole() and block.block_type == "dram" and self.context.use_noc1:
                    # Skip DRAM tests on wormhole devices when using NOC1 due to bug #tt-umd:1823
                    continue

                # Get all blocks with NOC addresses
                blocks_with_noc = [
                    (name, info)
                    for name, info in memory_map._blocks_info.items()
                    if info.memory_block.address.noc_address is not None
                ]

                for block_name, block_info in blocks_with_noc:
                    # Skip L1 on DRAM on Blackhole devices due to bug #tt-umd:1873
                    if device.is_blackhole() and block_name == "l1" and block.block_type == "dram":
                        continue
                    # Skip control_regs on DRAM on Blackhole devices. It is safe to write, but not safe to write whatever you want
                    if device.is_blackhole() and block_name == "control_regs" and block.block_type == "dram":
                        continue
                    noc_addr = block_info.memory_block.address.noc_address
                    assert noc_addr is not None, "NOC address should not be None here"
                    size = block_info.memory_block.size
                    is_accessible = block_info.is_accessible
                    is_safe_to_read = block_info.is_safe_to_read(noc_addr, size)
                    is_safe_to_write = block_info.is_safe_to_write(noc_addr, size)

                    location_str = str(location)

                    # Test 1: Access fully inside the block (test all blocks including inaccessible)
                    self._test_access_inside_block(
                        device_id,
                        location_str,
                        block_name,
                        noc_addr,
                        size,
                        is_accessible,
                        is_safe_to_read,
                        is_safe_to_write,
                    )

                    # Only run spanning tests for accessible and readable blocks
                    if is_accessible and is_safe_to_read:
                        # Test 2: Access spanning into another readable block
                        self._test_access_spanning_readable(
                            device_id, location_str, block_name, block_info, memory_map, is_safe_to_write
                        )

                        # Test 3: Access spanning into unreadable/unknown region
                        self._test_access_spanning_unreadable(
                            device_id, location_str, block_name, noc_addr, size, is_safe_to_write, memory_map
                        )

    def _test_access_inside_block(
        self,
        device_id: int,
        location: str,
        block_name: str,
        noc_addr: int,
        size: int,
        is_accessible: bool,
        is_safe_to_read: bool,
        is_safe_to_write: bool,
    ):
        """Test access fully inside a block."""
        # Determine if we need use_4B_mode=True (for RISC private memory)
        use_4b_mode = None
        if "data_private_memory" in block_name:
            use_4b_mode = True

        # Determine test size (small enough to fit in block, min 4 bytes)
        span_size = min(64, size // 2, size - 4)
        if span_size < 4:
            return  # Skip tiny blocks

        start_addr = noc_addr + (size // 2) - 1

        # If block is not accessible, expect all accesses to fail
        if not is_accessible:
            # Test READ should fail
            with self.assertRaises(
                UnsafeAccessException,
                msg=f"Read from inaccessible block {block_name} at {location} should raise UnsafeAccessException",
            ):
                lib.read_from_device(
                    location,
                    start_addr,
                    device_id=device_id,
                    num_bytes=span_size,
                    use_4B_mode=use_4b_mode,
                    context=self.context,
                )

            # Test WRITE should fail
            data = bytes([0xAB] * span_size)
            with self.assertRaises(
                UnsafeAccessException,
                msg=f"Write to inaccessible block {block_name} at {location} should raise UnsafeAccessException",
            ):
                lib.write_to_device(
                    location, start_addr, data, device_id=device_id, use_4B_mode=use_4b_mode, context=self.context
                )
            return

        # Test READ for accessible blocks
        if is_safe_to_read:
            result = lib.read_from_device(
                location,
                start_addr,
                device_id=device_id,
                num_bytes=span_size,
                use_4B_mode=use_4b_mode,
                context=self.context,
            )
            self.assertEqual(
                len(result),
                span_size,
                f"Read from {block_name} at {location} should return {span_size} bytes from address {start_addr}",
            )
        else:
            # Should raise exception
            with self.assertRaises(
                UnsafeAccessException,
                msg=f"Read from unsafe block {block_name} at {location} should raise UnsafeAccessException",
            ):
                lib.read_from_device(
                    location,
                    start_addr,
                    device_id=device_id,
                    num_bytes=span_size,
                    use_4B_mode=use_4b_mode,
                    context=self.context,
                )

        # Test WRITE
        if is_safe_to_write:
            data = bytes([i % 256 for i in range(span_size)])
            lib.write_to_device(
                location, start_addr, data, device_id=device_id, use_4B_mode=use_4b_mode, context=self.context
            )

            # Verify by reading back (skip debug registers block - they don't guarantee read-back of written values)
            if is_safe_to_read and block_name != "debug_regs":
                result = lib.read_from_device(
                    location,
                    start_addr,
                    device_id=device_id,
                    num_bytes=span_size,
                    use_4B_mode=use_4b_mode,
                    context=self.context,
                )
                self.assertEqual(
                    result,
                    data,
                    f"Read-back after write to {block_name} at {location} should match written data at address {start_addr}",
                )
        else:
            # Should raise exception
            data = bytes([0xAB] * span_size)
            with self.assertRaises(
                UnsafeAccessException,
                msg=f"Write to read-only block {block_name} at {location} should raise UnsafeAccessException",
            ):
                lib.write_to_device(
                    location,
                    start_addr,
                    data,
                    device_id=device_id,
                    safe_mode=True,
                    use_4B_mode=use_4b_mode,
                    context=self.context,
                )

    def _test_access_spanning_readable(
        self,
        device_id: int,
        location: str,
        block_name: str,
        block_info: MemoryMapBlockInfo,
        memory_map: MemoryMap,
        is_safe_to_write: bool,
    ):
        """Test access spanning from this block into an adjacent readable block."""
        noc_addr = block_info.memory_block.address.noc_address
        assert noc_addr is not None, "NOC address should not be None here"
        size = block_info.memory_block.size
        block_end = noc_addr + size

        # Find the next block (if any)
        next_block_info = memory_map.find_next_by_noc_address(block_end)
        if next_block_info is None:
            return  # No next block

        next_noc_addr = next_block_info.memory_block.address.noc_address
        assert next_noc_addr is not None, "NOC address should not be None here"
        next_is_accessible = next_block_info.is_accessible
        next_is_safe_to_read = next_block_info.is_safe_to_read(next_noc_addr, 4)
        next_is_safe_to_write = next_block_info.is_safe_to_write(next_noc_addr, 4)

        # Check if blocks are adjacent (no gap), accessible, and readable
        if next_noc_addr != block_end or not next_is_accessible or not next_is_safe_to_read:
            return

        # Calculate span size (half in each block)
        span_size = min(32, size // 2, next_block_info.memory_block.size // 2)
        if span_size < 8:
            return  # Too small to span meaningfully

        start_addr = block_end - span_size // 2

        # Determine if we need use_4B_mode=True
        use_4b_mode = None
        if "data_private_memory" in block_name or "data_private_memory" in next_block_info.name:
            use_4b_mode = True

        # Test READ spanning two blocks
        result = lib.read_from_device(
            location, start_addr, num_bytes=span_size, use_4B_mode=use_4b_mode, context=self.context
        )
        self.assertEqual(
            len(result), span_size, f"Read spanning {block_name} -> {next_block_info.name} at {location} should succeed"
        )

        # Test WRITE spanning two blocks
        if is_safe_to_write and next_is_safe_to_write:
            data = bytes([i % 256 for i in range(span_size)])
            lib.write_to_device(
                location, start_addr, data, device_id=device_id, use_4B_mode=use_4b_mode, context=self.context
            )

            # Verify by reading back if both are readable
            result = lib.read_from_device(
                location,
                start_addr,
                device_id=device_id,
                num_bytes=span_size,
                use_4B_mode=use_4b_mode,
                context=self.context,
            )
            self.assertEqual(
                result, data, f"Read-back after spanning write {block_name} -> {next_block_info.name} should match"
            )

    def _test_access_spanning_unreadable(
        self,
        device_id: int,
        location: str,
        block_name: str,
        noc_addr: int,
        size: int,
        is_safe_to_write: bool,
        memory_map: MemoryMap,
    ):
        """Test access spanning from this block into an unreadable/unmapped region."""
        block_end = noc_addr + size

        # Find the next block (if any) - use block_end - 1 to find blocks that start at or after block_end
        next_block_info = memory_map.find_next_by_noc_address(block_end - 1)

        # Determine if there's actually a gap
        has_gap = (
            next_block_info is None or next_block_info.memory_block.address.noc_address > block_end  # type: ignore[operator]
        )

        # Case 1: There's a gap after this block (unmapped region)
        if has_gap:
            # Try to read/write spanning into the gap
            span_size = min(64, size // 2) if size > 8 else 8
            start_addr = block_end - span_size // 2

            # Read spanning into gap should fail (only test for readable blocks)
            with self.assertRaises(
                UnsafeAccessException,
                msg=f"Read spanning {block_name} into unmapped gap at {location} should raise UnsafeAccessException",
            ):
                lib.read_from_device(
                    location, start_addr, device_id=device_id, num_bytes=span_size, context=self.context
                )

            # Write spanning into gap should fail (only test for writable blocks)
            if is_safe_to_write:
                data = bytes([0xCC] * span_size)
                with self.assertRaises(
                    UnsafeAccessException,
                    msg=f"Write spanning {block_name} into unmapped gap at {location} should raise UnsafeAccessException",
                ):
                    lib.write_to_device(location, start_addr, data, device_id=device_id, context=self.context)
        # Case 2: Next block is adjacent but not accessible or has incompatible permissions
        elif next_block_info is not None and next_block_info.memory_block.address.noc_address == block_end:
            next_noc_addr = next_block_info.memory_block.address.noc_address
            assert next_noc_addr is not None, "NOC address should not be None here"
            next_is_accessible = next_block_info.is_accessible
            next_is_safe_to_read = next_block_info.is_safe_to_read(next_noc_addr, 4)
            next_is_safe_to_write = next_block_info.is_safe_to_write(next_noc_addr, 4)

            # Test spanning into inaccessible block
            if not next_is_accessible or not next_is_safe_to_read:
                span_size = min(32, size // 2, next_block_info.memory_block.size // 2)
                if span_size >= 8:
                    start_addr = block_end - span_size // 2

                    with self.assertRaises(
                        UnsafeAccessException,
                        msg=f"Read spanning {block_name} into inaccessible/not safe to read {next_block_info.name} at {location} should raise UnsafeAccessException",
                    ):
                        lib.read_from_device(
                            location, start_addr, device_id=device_id, num_bytes=span_size, context=self.context
                        )

            # Test spanning from writable to non-writable
            elif not next_is_safe_to_write:
                span_size = min(32, size // 2, next_block_info.memory_block.size // 2)
                if span_size >= 8:
                    start_addr = block_end - span_size // 2
                    data = bytes([0xDD] * span_size)

                    with self.assertRaises(
                        UnsafeAccessException,
                        msg=f"Write spanning {block_name} (writable) into {next_block_info.name} (read-only) at {location} should raise UnsafeAccessException",
                    ):
                        lib.write_to_device(location, start_addr, data, device_id=device_id, context=self.context)


class TestRunElf(unittest.TestCase):
    context: Context
    device: Device

    @classmethod
    def setUpClass(cls) -> None:
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]

    def get_elf_path(self, app_name: str, risc_name: str):
        """Get the path to the ELF file."""
        arch = str(self.device._arch).lower()
        if arch == "wormhole_b0":
            arch = "wormhole"
        risc = risc_name.lower()
        return f"build/riscv-src/{arch}/{app_name}.{risc}.elf"

    RUN_ELF_TEST_ELFS = ["run_elf_test.debug", "run_elf_test.release", "run_elf_test.coverage"]
    RISCS = ["brisc", "trisc0", "trisc1", "trisc2", "ncrisc"]

    @parameterized.expand(itertools.product(RUN_ELF_TEST_ELFS, RISCS))
    def test_run_elf(self, elf_name: str, risc_name: str):
        """Test running an ELF file."""
        location = "0,0"

        # The mailbox lives in the per-RISC thread_local region, so resolve its
        # address from the ELF instead of assuming a fixed one (the old 0x64000
        # was out of range on smaller L1s such as ETH).
        elf_path = self.get_elf_path(elf_name, risc_name)
        elf = get_parsed_elf_file(elf_path)
        mailbox_die = elf.find_die_by_name("mailbox")
        assert mailbox_die is not None, f"mailbox symbol not found in {elf_path}"
        addr = mailbox_die.get_address()
        assert addr is not None, f"could not resolve mailbox address in {elf_path}"

        # Reset memory at addr
        lib.write_words_to_device(location, addr, 0, context=self.context)
        ret = lib.read_words_from_device(location, addr, context=self.context)
        self.assertEqual(ret[0], 0)

        # Run an ELF that writes to the mailbox and check if it executed correctly
        lib.run_elf(elf, location, risc_name, context=self.context)
        ret = lib.read_words_from_device(location, addr, context=self.context)
        self.assertEqual(ret[0], 0x12345678)

    @parameterized.expand(
        [
            ("", "0,0", "brisc", 0),  # Invalid ELF path
            ("/sbin/non_existing_elf", "0,0", "brisc", 0),  # Invalid ELF path
            (None, "abcd", "brisc", 0),  # Invalid location
            (None, "-10", "brisc", 0),  # Invalid location
            (None, "0,0/", "brisc", 0),  # Invalid location
            (None, "0,0/00b", "brisc", 0),  # Invalid location
            (None, "0,0", "invalid", 0),  # Invalid risc_name
            (None, "0,0", "brisc", -1),  # Invalid device_id
            (None, "0,0", "brisc", 112),  # Invalid device_id (too high)
        ]
    )
    def test_run_elf_invalid(self, elf_file, location, risc_name, device_id):
        if elf_file is None:
            elf_file = self.get_elf_path("run_elf_test.debug", "brisc")
        with self.assertRaises((TTException, ValueError)):
            lib.run_elf(elf_file, location, risc_name, None, device_id, context=self.context)

    @parameterized.expand(
        [
            ("brisc"),
            ("trisc0"),
            ("trisc1"),
            ("trisc2"),
        ]
    )
    def test_old_elf_test(self, risc_name: str):
        if self.device.is_blackhole():
            self.skipTest("This test doesn't work as expected on blackhole. Disabling it until bug #120 is fixed.")

        """ Running old elf test, formerly done with -t option. """
        location = "0,0"
        elf_path = self.get_elf_path("sample.debug", risc_name)
        elf = get_parsed_elf_file(elf_path)
        lib.run_elf(elf, location, risc_name, context=self.context)

        # Testing
        loc = OnChipCoordinate.create(location, device=self.device)
        device = loc._device
        noc_block = device.get_block(loc)
        risc_debug = noc_block.get_risc_debug(risc_name)
        assert isinstance(risc_debug, BabyRiscDebug), f"Expected BabyRiscDebug, got {type(risc_debug)}"
        rdbg: BabyRiscDebug = risc_debug
        assert rdbg.debug_hardware is not None, "Debug hardware is not available."

        elf = lib.parse_elf(elf_path)
        mem_access = create_memory_access(risc_debug)
        mailbox = elf.get_global("g_MAILBOX", mem_access)
        testbyteaccess = elf.get_global("g_TESTBYTEACCESS", mem_access)

        # Disable branch rediction due to bne instruction in the elf
        rdbg.set_branch_prediction(False)

        # Step 0: halt and continue a couple of times.
        def halt_cont_test():
            rdbg.halt()
            assert rdbg.is_halted(), f"RISC at location {loc} is not halted."
            rdbg.cont()
            assert not rdbg.is_halted(), f"RISC at location {loc} is halted."
            rdbg.halt()
            assert rdbg.is_halted(), f"RISC at location {loc} is not halted."
            rdbg.cont()
            assert not rdbg.is_halted(), f"RISC at location {loc} is halted."

        halt_cont_test()

        # Step 1: Check that the RISC at location {loc} set the mailbox value to 0xFFB1208C.
        self.assertEqual(mailbox, 0xFFB1208C, f"RISC at location {loc} did not set the mailbox value to 0xFFB1208C.")
        # TODO: Add this back in once we get a library version: gpr_command["module"].run("gpr pc,sp", context, ui_state)

        # Step 2: Write 0x1234 to the mailbox to resume operation.
        try:
            mailbox.write_value(0x1234)
        except Exception as e:
            if e.args[0].startswith("Failed to continue"):
                # We are expecting this to assert as here, the core will halt istself by calling halt()
                pass
            else:
                raise e

        # Step 3: Check that the RISC at location {loc} set the mailbox value to 0xFFB12080.
        self.assertEqual(mailbox, 0xFFB12080, f"RISC at location {loc} did not set the mailbox value to 0xFFB12080.")

        # Step 4: Check that the RISC at location {loc} is halted.
        status = rdbg.debug_hardware.read_status()
        # print_PC_and_source(rdbg.read_gpr(32), elf)
        self.assertTrue(status.is_halted, f"Step 4: RISC at location {loc} is not halted.")
        self.assertTrue(status.is_ebreak_hit, f"Step 4: RISC at location {loc} is not halted with ebreak.")

        # Step 5a: Make sure that the core did not reach step 5
        self.assertNotEqual(mailbox, 0xFFB12088, f"RISC at location {loc} reached step 5, but it should not have.")

        # Step 5b: Continue and check that the core reached 0xFFB12088. But first set the breakpoint at
        # function "decrement_mailbox"
        from ttexalens.elf import DwarfDieTag

        decrement_mailbox_die = elf.find_die_by_name("decrement_mailbox")
        assert decrement_mailbox_die is not None, "decrement_mailbox function not found in ELF."
        assert (
            decrement_mailbox_die.tag == DwarfDieTag.subprogram
        ), f"decrement_mailbox DIE is not a subprogram, got {decrement_mailbox_die.tag}"
        decrement_mailbox_address = decrement_mailbox_die.get_address()

        # Step 6. Setting breakpoint at decrement_mailbox
        watchpoint_id = 1  # Out of 8
        rdbg.debug_hardware.set_watchpoint_on_pc_address(watchpoint_id, decrement_mailbox_address)
        rdbg.debug_hardware.set_watchpoint_on_memory_write(
            0, testbyteaccess.get_address()
        )  # Set memory watchpoint on TESTBYTEACCESS
        rdbg.debug_hardware.set_watchpoint_on_memory_write(3, testbyteaccess.get_address() + 3)
        rdbg.debug_hardware.set_watchpoint_on_memory_write(4, testbyteaccess.get_address() + 4)
        rdbg.debug_hardware.set_watchpoint_on_memory_write(5, testbyteaccess.get_address() + 5)

        mbox_val: int = 1
        timeout_retries = 20
        while mbox_val >= 0 and mbox_val < 0xFF000000 and timeout_retries > 0:
            if rdbg.is_halted():
                if rdbg.debug_hardware.is_pc_watchpoint_hit():
                    pass  # util.INFO (f"Breakpoint hit.")

            try:
                rdbg.cont()
            except Exception as e:
                if e.args[0].startswith("Failed to continue"):
                    # We are expecting this to assert as here, the core will hit a breakpoint
                    pass
                else:
                    raise e
            mbox_val = mailbox.read_value()  # type: ignore
            # Step 5b: Continue RISC
            timeout_retries -= 1

        if timeout_retries == 0 and mbox_val != 0:
            raise util.TTFatalException(f"RISC at location {loc} did not get past step 6.")
        self.assertFalse(
            rdbg.debug_hardware.is_pc_watchpoint_hit(),
            f"RISC at location {loc} hit the breakpoint but it should not have.",
        )

        # STEP 7: Testing byte access memory watchpoints")
        self.assertEqual(mailbox, 0xFF000003, f"RISC at location {loc} did not set the mailbox value to 0xff000003.")
        status = rdbg.debug_hardware.read_status()
        self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
        if not status.is_memory_watchpoint_hit or not status.watchpoints_hit[3]:
            raise util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 3.")
        rdbg.cont()

        self.assertEqual(mailbox, 0xFF000005, f"RISC at location {loc} did not set the mailbox value to 0xff000005.")
        status = rdbg.debug_hardware.read_status()
        self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
        if not status.is_memory_watchpoint_hit or not status.watchpoints_hit[5]:
            raise util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 5.")
        rdbg.cont()

        self.assertEqual(mailbox, 0xFF000000, f"RISC at location {loc} did not set the mailbox value to 0xff000000.")
        status = rdbg.debug_hardware.read_status()
        self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
        if not status.is_memory_watchpoint_hit or not status.watchpoints_hit[0]:
            raise util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 0.")
            return False
        rdbg.cont()

        self.assertEqual(mailbox, 0xFF000004, f"RISC at location {loc} did not set the mailbox value to 0xff000004.")
        status = rdbg.debug_hardware.read_status()
        self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
        if not status.is_memory_watchpoint_hit or not status.watchpoints_hit[4]:
            raise util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 4.")
        rdbg.cont()

        # STEP END:
        self.assertEqual(mailbox, 0xFFB12088, f"RISC at location {loc} did not reach step STEP END.")

        # Enable branch prediction
        rdbg.set_branch_prediction(True)


class TestARC(unittest.TestCase):
    context: Context
    device: Device

    @classmethod
    def setUpClass(cls) -> None:
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]

    def test_arc_msg(self):
        """Test getting AICLK from ARC."""

        if self.device.is_blackhole():
            self.skipTest("Arc message is not supported on blackhole UMD")

        msg_code = 0x90  # ArcMessageType::TEST
        wait_for_done = True
        args = [0, 0]
        timeout = timedelta(milliseconds=1000)

        # Ask for reply, check for reasonable TEST value
        ret, return_3, _ = lib.arc_msg(self.device.id, msg_code, wait_for_done, args, timeout, context=self.context)

        print(f"ARC message result={ret}, test={return_3}")
        self.assertEqual(ret, 0)

        # Asserting that return_3 (test) is 0
        # TODO: self.assertEqual(return_3, 0)

    fw_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../..", "fw/arc/arc_bebaceca.hex")

    def test_arc_heartbeat(self):
        """Test reading ARC heartbeat"""
        if not self.device.is_wormhole() and not self.device.is_blackhole():
            self.skipTest("ARC telemetry is not supported for this architecture")

        if self.device.firmware_version < CUTOFF_FIRMWARE_VERSION:
            self.skipTest(f"ARC telemetry is not supported for firmware version {self.device.firmware_version}")

        tag = "TIMER_HEARTBEAT"

        # Check if heartbeat is increasing
        import time

        heartbeat1 = lib.read_arc_telemetry_entry(self.device.id, tag)
        time.sleep(0.2)
        heartbeat2 = lib.read_arc_telemetry_entry(self.device.id, tag)
        self.assertGreater(heartbeat2, heartbeat1)

    @parameterized.expand(
        [
            ("BOARD_ID_HIGH", 1),
            ("BOARD_ID_LOW", 2),
            ("AICLK", 14),
            ("AXICLK", 15),
            ("ARCCLK", 16),
        ]
    )
    def test_read_arc_telemetry_entry(self, tag_name, tag_id):
        """Test if reading ARC telemetry entry by tag name and tag ID gives the same result"""

        if not self.device.is_wormhole() and not self.device.is_blackhole():
            self.skipTest("ARC telemetry is not supported for this architecture")

        if self.device.firmware_version < CUTOFF_FIRMWARE_VERSION:
            self.skipTest(f"ARC telemetry is not supported for firmware version {self.device.firmware_version}")

        ret_from_name = lib.read_arc_telemetry_entry(self.device.id, tag_name)
        ret_from_id = lib.read_arc_telemetry_entry(self.device.id, tag_id)
        self.assertEqual(ret_from_name, ret_from_id)

    def test_load_arc_fw(self):

        if self.device.is_blackhole():
            self.skipTest("Loading ARC firmware is not supported on blackhole")

        for device_id in self.context.device_ids:
            device = self.context.devices[device_id]
            arc = device.arc_block
            arc.load_arc_fw(self.fw_file_path, 2)
            scratch2 = arc.get_register_store().read_register("ARC_RESET_SCRATCH2")
            assert scratch2 == 0xBEBACECA


@parameterized_class(
    [
        {"location_desc": "ETH0", "risc_name": "ERISC"},
        {"location_desc": "ETH0", "risc_name": "ERISC0"},
        {"location_desc": "ETH0", "risc_name": "ERISC1"},
        {"location_desc": "FW0", "risc_name": "BRISC"},
        {"location_desc": "FW0", "risc_name": "TRISC0"},
        {"location_desc": "FW0", "risc_name": "TRISC1"},
        {"location_desc": "FW0", "risc_name": "TRISC2"},
        {"location_desc": "DRAM0", "risc_name": "DRISC"},
    ]
)
class TestCallStack(unittest.TestCase):
    risc_name: str  # Risc name
    risc_id: int  # Risc ID - being parametrized
    context: Context  # TTExaLens context
    location_desc: str  # Core description ETH0, FW0, FW1 - being parametrized
    location: OnChipCoordinate  # Core location
    risc_debug: RiscDebug  # RiscDebug object
    loader: ElfLoader  # ElfLoader object
    pc_register_index: int  # PC register index
    device: Device  # Device
    gdb_server: GdbServer  # GDB server

    @classmethod
    def setUpClass(cls):
        cls.context = init_cached_test_context()
        cls.device = cls.context.devices[0]
        server = ServerSocket()
        server.start()
        cls.gdb_server = GdbServer(cls.context, server, skip_detach=True, debug_only_with_elfs=True)
        cls.gdb_server.start()

    @classmethod
    def tearDownClass(cls):
        cls.gdb_server.stop()

    def setUp(self):
        try:
            self.location = get_core_location(self.location_desc, self.device)
        except ValueError:
            # If not found, we should skip the test
            self.skipTest("Location is not available on this platform")

        noc_block = self.location._device.get_block(self.location)
        try:
            self.risc_debug = noc_block.get_risc_debug(self.risc_name)
            self.risc_name = self.risc_debug.risc_location.risc_name
        except ValueError:
            self.skipTest(f"{self.risc_name} core is not available in this block on this platform")
        except NotImplementedError:
            self.skipTest(f"{self.risc_name} core is not available in this block on this platform")

        self.loader = ElfLoader(self.risc_debug)
        self.l1_mem_access = create_l1_memory_access(self.location)

        # Stop risc with reset
        self.risc_debug.set_reset_signal(True)
        self.assertTrue(self.risc_debug.is_in_reset())

    def tearDown(self):
        # Stop risc with reset
        self.risc_debug.set_reset_signal(True)
        self.assertTrue(self.risc_debug.is_in_reset())

    def is_eth_block(self):
        """Check if the core is ETH."""
        return self.device.get_block_type(self.location) == "eth"

    def get_elf_path(self, app_name):
        """Get the path to the ELF file."""
        arch = str(self.device._arch).lower()
        if arch == "wormhole_b0":
            arch = "wormhole"
        return f"build/riscv-src/{arch}/{app_name}.{self.risc_name.lower()}.elf"

    def compare_callstacks(self, cs1: list[CallstackEntry], cs2: list[CallstackEntry]):
        """Compare two callstacks."""
        self.assertEqual(len(cs1), len(cs2), "Callstacks have different lengths")
        for entry1, entry2 in zip(cs1, cs2):
            self.assertEqual(entry1.function_name, entry2.function_name, "Function names do not match")
            file1 = entry1.file_info.file if entry1.file_info is not None else None
            file2 = entry2.file_info.file if entry2.file_info is not None else None
            line1 = entry1.file_info.line if entry1.file_info is not None else None
            line2 = entry2.file_info.line if entry2.file_info is not None else None
            self.assertEqual(file1, file2, "Source files do not match")
            self.assertEqual(line1, line2, "Line numbers do not match")
            if entry1.pc is not None and entry2.pc is not None:
                self.assertEqual(entry1.pc, entry2.pc, "Addresses do not match")

    def set_recursion_count(self, elf: ElfFile, count: int):
        text_section = elf.get_section_by_name(".text")
        assert text_section is not None
        assert text_section.address is not None

        address = text_section.address + text_section.size
        self.l1_mem_access.write(address, count.to_bytes(4, byteorder="little"))

    CALLSTACK_ELFS = ["callstack.debug", "callstack.release", "callstack.coverage"]
    RECURSION_COUNT = [1, 10, 40]

    @parameterized.expand(itertools.product(CALLSTACK_ELFS, RECURSION_COUNT))
    def test_callstack_with_parsing(self, elf_name: str, recursion_count: int):
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, recursion_count)
        self.loader.run_elf(parsed_elf)

        mem_access = create_memory_access(self.risc_debug)
        parsed_elf.get_global("g_MAILBOX", mem_access)

        callstack: list[CallstackEntry] = lib.callstack(
            self.location, parsed_elf, None, self.risc_name, None, 100, True
        )
        self.assertEqual(len(callstack), recursion_count + 3)
        self.assertEqual(callstack[0].function_name, "halt")
        for i in range(1, recursion_count + 1):
            self.assertEqual(callstack[i].function_name, "f1")
        self.assertEqual(callstack[recursion_count + 1].function_name, "recurse")
        self.assertEqual(callstack[recursion_count + 2].function_name, "main")
        gdb_callstack: list[CallstackEntry] = get_gdb_callstack(
            self.location, self.risc_name, [elf_path], [None], self.gdb_server
        )
        self.compare_callstacks(callstack, gdb_callstack)

    def test_callstack(self):
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        # No need to test multiple versions here, they are tested in test_callstack_with_parsing. Here we just test that callstack works with elf path.
        elf_name = "callstack.release"
        recursion_count = 1
        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, recursion_count)
        self.loader.run_elf(parsed_elf)
        callstack: list[CallstackEntry] = lib.callstack(self.location, elf_path, None, self.risc_name, None, 100, True)
        self.assertEqual(len(callstack), recursion_count + 3)
        self.assertEqual(callstack[0].function_name, "halt")
        for i in range(1, recursion_count + 1):
            self.assertEqual(callstack[i].function_name, "f1")
        self.assertEqual(callstack[recursion_count + 1].function_name, "recurse")
        self.assertEqual(callstack[recursion_count + 2].function_name, "main")
        gdb_callstack: list[CallstackEntry] = get_gdb_callstack(
            self.location, self.risc_name, [elf_path], [None], self.gdb_server
        )
        self.compare_callstacks(callstack, gdb_callstack)

    @parameterized.expand(CALLSTACK_ELFS)
    def test_callstack_namespace(self, elf_name):
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, 0)
        self.loader.run_elf(parsed_elf)
        callstack: list[CallstackEntry] = lib.callstack(
            self.location, parsed_elf, None, self.risc_name, None, 100, True
        )
        self.assertEqual(len(callstack), 3)
        self.assertEqual(callstack[0].function_name, "halt")
        self.assertEqual(callstack[1].function_name, "ns::foo")
        self.assertEqual(callstack[2].function_name, "main")
        gdb_callstack: list[CallstackEntry] = get_gdb_callstack(
            self.location, self.risc_name, [elf_path], [None], self.gdb_server
        )
        self.compare_callstacks(callstack, gdb_callstack)

    @parameterized.expand(CALLSTACK_ELFS)
    def test_callstack_tail_call(self, elf_name):
        # 0xFFFFFFFA selects the tail_call_test chain in callstack.cc. In the optimized build ra1
        # tail-calls pc1 (the call becomes a jump), so the ra1 frame - with its inlined ra2/ra3 -
        # leaves no return address on the stack and is only recoverable from the DWARF call-site
        # (tail-call) information. In the -O0 (debug / coverage) build the same logical stack is
        # produced through ordinary unwinding. GDB reconstructs the tail-called frame in both cases,
        # so it is the ground truth our walker must match regardless of optimization level.
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, 0xFFFFFFFA)
        self.loader.run_elf(parsed_elf)
        callstack: list[CallstackEntry] = lib.callstack(
            self.location, parsed_elf, None, self.risc_name, None, 100, True
        )

        # The inlined leaf chain (halt inlined into pc3/pc2/pc1) is reconstructed from the PC alone,
        # so it appears the same way on every build; run() and main() anchor the bottom of the walk.
        # The tail-called ra* frames in between differ by optimization level, so they are validated
        # through the GDB comparison rather than pinned here.
        leading = ["halt", "tail_call_test::pc3", "tail_call_test::pc2", "tail_call_test::pc1"]
        for index, expected in enumerate(leading):
            # As elsewhere, an optimized clone of a leaf can lose its namespace qualification.
            self.assertIn(callstack[index].function_name, (expected, expected.split("::")[-1]))
        self.assertIn(callstack[-2].function_name, ("tail_call_test::run", "run"))
        self.assertEqual(callstack[-1].function_name, "main")

        gdb_callstack: list[CallstackEntry] = get_gdb_callstack(
            self.location, self.risc_name, [elf_path], [None], self.gdb_server
        )
        self.compare_callstacks(callstack, gdb_callstack)

    @parameterized.expand(CALLSTACK_ELFS)
    def test_callstack_tail_call_expand_inline_frames(self, elf_name):
        # With expand_tail_call_inline_frames=True a reconstructed tail-call frame is expanded into
        # its full inlined-function chain (ra3 <- ra2 <- ra1) instead of GDB's single innermost frame.
        # The inline structure is read straight from the call-site PC, so the result is identical on
        # every build: the optimized build reconstructs ra2/ra1 from the tail-call info, while the -O0
        # builds get them from ordinary inline expansion. The whole source-level chain is therefore
        # pinned exactly here (this mode intentionally diverges from GDB, so there is no GDB compare).
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, 0xFFFFFFFA)
        self.loader.run_elf(parsed_elf)
        callstack: list[CallstackEntry] = lib.callstack(
            self.location, parsed_elf, None, self.risc_name, None, 100, True, expand_tail_call_inline_frames=True
        )

        expected = [
            "halt",
            "tail_call_test::pc3",
            "tail_call_test::pc2",
            "tail_call_test::pc1",
            "tail_call_test::ra3",
            "tail_call_test::ra2",
            "tail_call_test::ra1",
            "tail_call_test::run",
            "main",
        ]
        self.assertEqual(len(callstack), len(expected))
        for entry, name in zip(callstack, expected):
            # As elsewhere, an optimized clone of a leaf can lose its namespace qualification.
            self.assertIn(entry.function_name, (name, name.split("::")[-1]))

    @parameterized.expand(CALLSTACK_ELFS)
    def test_callstack_tail_call_chain(self, elf_name):
        # 0xFFFFFFF9 selects the tail_chain_test chain in callstack.cc: tc_a tail-calls tc_b, tc_b
        # tail-calls tc_c, tc_c tail-calls tc_d - three separate tail-call edges in a row. In the
        # optimized build only run() and tc_d() remain as physical frames, so the tc_a/tc_b/tc_c
        # frames are recovered by following the multi-edge DWARF tail-call chain (exercising the
        # chain length > 1 path). GDB reconstructs the same frames, so it is the ground truth.
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, 0xFFFFFFF9)
        self.loader.run_elf(parsed_elf)
        callstack: list[CallstackEntry] = lib.callstack(
            self.location, parsed_elf, None, self.risc_name, None, 100, True
        )

        # tc_a/tc_b/tc_c are not inlined, so the whole chain appears the same on every build: the
        # optimized build reconstructs them from the tail-call info, the -O0 builds from ordinary
        # unwinding. halt() is the (inlined) leaf of tc_d; run() and main() anchor the bottom.
        expected = [
            "halt",
            "tail_chain_test::tc_d",
            "tail_chain_test::tc_c",
            "tail_chain_test::tc_b",
            "tail_chain_test::tc_a",
            "tail_chain_test::run",
            "main",
        ]
        self.assertEqual(len(callstack), len(expected))
        for entry, name in zip(callstack, expected):
            # As elsewhere, an optimized clone of a leaf can lose its namespace qualification.
            self.assertIn(entry.function_name, (name, name.split("::")[-1]))

        gdb_callstack: list[CallstackEntry] = get_gdb_callstack(
            self.location, self.risc_name, [elf_path], [None], self.gdb_server
        )
        self.compare_callstacks(callstack, gdb_callstack)

    @parameterized.expand([(x,) for x in RECURSION_COUNT])
    def test_top_callstack_with_parsing(self, recursion_count: int):
        elf_path = self.get_elf_path("callstack.debug")
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, recursion_count)
        self.loader.run_elf(parsed_elf)
        with self.risc_debug.ensure_halted():
            pc = self.risc_debug.read_gpr(32)
        callstack: list[CallstackEntry] = lib.top_callstack(pc, parsed_elf, None, self.context)
        self.assertEqual(len(callstack), 1)
        self.assertEqual(callstack[0].function_name, "halt")

    def test_top_callstack(self):
        # No need to test multiple versions here, they are tested in test_top_callstack_with_parsing. Here we just test that top_callstack works with elf path.
        recursion_count = 1
        elf_path = self.get_elf_path("callstack.debug")
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, recursion_count)
        self.loader.run_elf(parsed_elf)
        with self.risc_debug.ensure_halted():
            pc = self.risc_debug.read_gpr(32)
        callstack: list[CallstackEntry] = lib.top_callstack(pc, elf_path, None, self.context)
        self.assertEqual(len(callstack), 1)
        self.assertEqual(callstack[0].function_name, "halt")

    @parameterized.expand([(1, 1)])
    def test_top_callstack_optimized(self, recursion_count: int, expected_f1_on_callstack_count: int):
        elf_path = self.get_elf_path("callstack.release")
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, recursion_count)
        self.loader.run_elf(parsed_elf)
        with self.risc_debug.ensure_halted():
            pc = self.risc_debug.read_gpr(32)
        callstack: list[CallstackEntry] = lib.top_callstack(pc, parsed_elf, None, self.context)

        if self.device.is_blackhole() or self.device.is_wormhole():
            # The core halts on the ebreak inside halt(). The reported PC is the instruction after the
            # ebreak, which lands in the NOP padding emitted by -mtt-fix-whbhebreak; that padding is
            # attributed to halt() (callstack.cc:30), so halt() is the innermost (inlined) frame,
            # followed by the f1 frame(s) and recurse.
            self.assertEqual(len(callstack), expected_f1_on_callstack_count + 2)
            self.assertEqual(callstack[0].function_name, "halt")
            for i in range(0, expected_f1_on_callstack_count):
                self.assertEqual(callstack[1 + i].function_name, "f1")
            self.assertEqual(callstack[1 + expected_f1_on_callstack_count].function_name, "recurse")
        else:
            self.assertEqual(len(callstack), expected_f1_on_callstack_count + 1)
            for i in range(0, expected_f1_on_callstack_count):
                self.assertEqual(callstack[i].function_name, "f1")
            self.assertEqual(callstack[expected_f1_on_callstack_count + 0].function_name, "recurse")

    @parameterized.expand(CALLSTACK_ELFS)
    def test_template_arguments(self, elf_name):
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, 0xFFFFFFFF)
        self.loader.run_elf(parsed_elf)
        callstack: list[CallstackEntry] = lib.callstack(
            self.location, parsed_elf, None, self.risc_name, None, 100, True
        )
        self.assertEqual(len(callstack), 6)
        self.assertEqual(callstack[0].function_name, "halt")
        self.assertEqual(callstack[1].function_name, "f1")
        self.assertEqual(callstack[2].function_name, "f1")
        self.assertEqual(callstack[3].function_name, "recurse")
        self.assertEqual(callstack[4].function_name, "template_test::TemplateClass<3>::static_method<-1>")
        self.assertEqual(len(callstack[4].template_parameters), 2)
        self.assertEqual(callstack[4].template_parameters[0].name, "FunctionT1")
        self.assertEqual(callstack[4].template_parameters[0].value, -1)
        self.assertEqual(callstack[4].template_parameters[1].name, "ClassT1")
        self.assertEqual(callstack[4].template_parameters[1].value, 3)
        self.assertEqual(callstack[5].function_name, "main")

    @parameterized.expand(CALLSTACK_ELFS)
    def test_template_arguments2(self, elf_name):
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, 0xFFFFFFFE)
        self.loader.run_elf(parsed_elf)
        callstack: list[CallstackEntry] = lib.callstack(
            self.location, parsed_elf, None, self.risc_name, None, 100, True
        )
        self.assertEqual(len(callstack), 5)
        self.assertEqual(callstack[0].function_name, "halt")
        self.assertEqual(callstack[1].function_name, "f1")
        self.assertEqual(callstack[2].function_name, "recurse")
        self.assertEqual(callstack[3].function_name, "template_test::TemplateClass<4>::static_method<-3>")
        self.assertEqual(len(callstack[3].template_parameters), 2)
        self.assertEqual(callstack[3].template_parameters[0].name, "FunctionT1")
        self.assertEqual(callstack[3].template_parameters[0].value, -3)
        self.assertEqual(callstack[3].template_parameters[1].name, "ClassT1")
        self.assertEqual(callstack[3].template_parameters[1].value, 4)
        self.assertEqual(callstack[4].function_name, "main")

    # Argument and local variable values used by every value-test scenario in callstack.cc. Each
    # entry is (chained_function, single_frame_type, struct_format, argument, local).
    VALUE_TEST_TYPES = [
        ("value_test_bool", "bool", "<?", True, False),
        ("value_test_uint8", "unsigned char", "<B", 200, 17),
        ("value_test_int8", "signed char", "<b", -100, 50),
        ("value_test_uint16", "short unsigned int", "<H", 60000, 1234),
        ("value_test_int16", "short int", "<h", -30000, 5678),
        ("value_test_uint32", "long unsigned int", "<I", 4000000000, 12345678),
        ("value_test_int32", "long int", "<i", -2000000000, 87654321),
        ("value_test_uint64", "long long unsigned int", "<Q", 18000000000000000000, 1234567890123),
        ("value_test_int64", "long long int", "<q", -9000000000000000000, 9876543210),
        ("value_test_float", "float", "<f", 3.5, -1.25),
        ("value_test_double", "double", "<d", 2.5, -7.75),
        (
            "value_test_charptr",
            "char const*",
            "g_test_string",
            "Tenstorrent callstack string",
            "Tenstorrent callstack string",
        ),
    ]

    def get_mailbox_value_address(self, elf: ElfFile) -> int:
        """Address of the host-written value buffer in callstack.cc (see mailbox_value_buffer())."""
        text_section = elf.get_section_by_name(".text")
        assert text_section is not None
        assert text_section.address is not None

        firmware_end: int = text_section.address + text_section.size
        return (firmware_end + 4 + 16) & ~15

    def get_symbol_address(self, elf: ElfFile, name: str) -> int:
        symbol = elf.find_symbol_by_name(name)
        assert symbol is not None and symbol.value is not None, f"Symbol {name} not found in ELF"
        return int(symbol.value)

    def pack_value_test_value(self, elf: ElfFile, struct_format: str, value):
        # If struct_format doesn't start with "<", it's not a raw value but a symbol name whose address we want to get and pack as a uint32_t.
        if struct_format.startswith("<"):
            return struct.pack(struct_format, value)
        return struct.pack("<I", self.get_symbol_address(elf, struct_format))

    def assert_value_equals(self, actual, expected):
        if isinstance(expected, float):
            self.assertAlmostEqual(actual, expected, places=6)
        else:
            self.assertEqual(actual, expected)

    def assert_variable(
        self, variable: CallstackEntryVariable, expected_name: str, expected_value, require_value: bool, message: str
    ):
        self.assertEqual(variable.name, expected_name, message)
        if variable.value is None:
            self.assertFalse(require_value, f"Could not read {message}")
        else:
            self.assert_value_equals(variable.value.read_value(), expected_value)

    def assert_string_pointer(self, variable: CallstackEntryVariable, expected_name: str, address: int, message: str):
        self.assertEqual(variable.name, expected_name, message)
        value = variable.value
        assert value is not None, f"Could not read {message}"
        self.assertEqual(value.dereference().get_address(), address, message)

    def check_chained_value_test(
        self, elf_name: str, mailbox: int, namespace: str, require_arguments: bool, wrapper: str | None = None
    ):
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)
        self.set_recursion_count(parsed_elf, mailbox)
        self.loader.run_elf(parsed_elf)
        callstack: list[CallstackEntry] = lib.callstack(
            self.location, parsed_elf, None, self.risc_name, None, 100, True
        )

        # The callstack is: halt, the value-test chain (one frame per type), an optional wrapper
        # frame, then main.
        self.assertEqual(len(callstack), len(self.VALUE_TEST_TYPES) + 2 + (1 if wrapper else 0))
        self.assertEqual(callstack[0].function_name, "halt")
        self.assertEqual(callstack[-1].function_name, "main")
        if wrapper is not None:
            # As with the chain leaf, the optimized debug info may drop the namespace prefix.
            self.assertIn(callstack[len(self.VALUE_TEST_TYPES) + 1].function_name, (wrapper, wrapper.split("::")[-1]))

        for index, (function, _, _, expected_arg, expected_local) in enumerate(self.VALUE_TEST_TYPES):
            entry = callstack[index + 1]
            function_name = f"{namespace}::{function}"
            # On the optimized build a constant-propagated clone of a leaf function can lose its
            # namespace qualification in the debug info, so accept the bare name there too.
            self.assertIn(entry.function_name, (function_name, function), f"Unexpected frame: {entry.function_name}")

            # Every value-test function has exactly one argument and one local variable.
            self.assertEqual(len(entry.arguments), 1, f"Unexpected arguments for {function_name}")
            self.assertEqual(len(entry.locals), 1, f"Unexpected locals for {function_name}")
            self.assert_variable(
                entry.arguments[0], "arg", expected_arg, require_arguments, f"argument of {function_name}"
            )
            self.assert_variable(entry.locals[0], "local", expected_local, True, f"local of {function_name}")

    @parameterized.expand(CALLSTACK_ELFS)
    def test_callstack_argument_and_local_values(self, elf_name: str):
        require_arguments = "release" not in elf_name
        # 0xFFFFFFFD selects the value_test chain (separate frames, one per type) in callstack.cc.
        self.check_chained_value_test(elf_name, 0xFFFFFFFD, "value_test", require_arguments)

    @parameterized.expand(CALLSTACK_ELFS)
    def test_callstack_inlined_argument_and_local_values(self, elf_name: str):
        # 0xFFFFFFFC selects the inline_value_test chain (inlined virtual frames) in callstack.cc.
        self.check_chained_value_test(elf_name, 0xFFFFFFFC, "inline_value_test", True, wrapper="inline_value_test::run")

    @parameterized.expand(itertools.product(CALLSTACK_ELFS, range(len(VALUE_TEST_TYPES))))
    def test_callstack_single_frame_argument_and_local_values(self, elf_name: str, type_index: int):
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        _, type_name, struct_format, expected_arg, expected_local = self.VALUE_TEST_TYPES[type_index]
        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)

        # Select the single-frame dispatch for this type, then provide the argument (offset 0)
        # and local (offset 8) values through the host-written value buffer.
        # 0xFFFFFE00 | type_index invokes single_frame_value_test::dispatch for that type.
        self.set_recursion_count(parsed_elf, 0xFFFFFE00 | type_index)
        mailbox_value_address = self.get_mailbox_value_address(parsed_elf)
        self.l1_mem_access.write(
            mailbox_value_address, self.pack_value_test_value(parsed_elf, struct_format, expected_arg)
        )
        self.l1_mem_access.write(
            mailbox_value_address + 8, self.pack_value_test_value(parsed_elf, struct_format, expected_local)
        )
        self.loader.run_elf(parsed_elf)
        callstack: list[CallstackEntry] = lib.callstack(
            self.location, parsed_elf, None, self.risc_name, None, 100, True
        )

        # The callstack is: value_test<T> (top frame), dispatch, main.
        top = callstack[0]
        self.assertEqual(top.function_name, f"single_frame_value_test::value_test<{type_name}>")
        self.assertEqual(len(top.arguments), 1)
        self.assertEqual(len(top.locals), 1)
        if struct_format.startswith("<"):
            self.assert_variable(top.arguments[0], "arg", expected_arg, True, f"argument of {top.function_name}")
            self.assert_variable(top.locals[0], "local", expected_local, True, f"local of {top.function_name}")
        else:
            # A const char* transferred through a register: verify it points at the test string.
            address = self.get_symbol_address(parsed_elf, struct_format)
            self.assert_string_pointer(top.arguments[0], "arg", address, f"argument of {top.function_name}")
            self.assert_string_pointer(top.locals[0], "local", address, f"local of {top.function_name}")

    @parameterized.expand(CALLSTACK_ELFS)
    def test_callstack_callee_saved_register_values(self, elf_name: str):
        if self.device.is_blackhole() and self.risc_name == "trisc2":
            self.skipTest("This test doesn't work as expected due to blackhole trisc2 hardware bug, tt-exalens:#528")

        elf_path = self.get_elf_path(elf_name)
        parsed_elf = get_parsed_elf_file(elf_path)
        mailbox_value_address = self.get_mailbox_value_address(parsed_elf)
        for index, (_, _, struct_format, value, _) in enumerate(self.VALUE_TEST_TYPES):
            self.l1_mem_access.write(
                mailbox_value_address + index * 8, self.pack_value_test_value(parsed_elf, struct_format, value)
            )
        # 0xFFFFFFFB selects the callee_saved_test chain (value per type in a callee-saved register).
        self.set_recursion_count(parsed_elf, 0xFFFFFFFB)
        self.loader.run_elf(parsed_elf)
        callstack: list[CallstackEntry] = lib.callstack(
            self.location, parsed_elf, None, self.risc_name, None, 100, True
        )

        # The callstack is: halt, the callee_saved_test chain (one frame per type), then main.
        self.assertEqual(len(callstack), len(self.VALUE_TEST_TYPES) + 2)
        self.assertEqual(callstack[0].function_name, "halt")
        self.assertEqual(callstack[-1].function_name, "main")
        for index, (function, _, struct_format, value, _) in enumerate(self.VALUE_TEST_TYPES):
            frame = callstack[index + 1]
            function_name = f"callee_saved_test::{function}"
            # As elsewhere, the optimized build can drop the namespace of a leaf function.
            self.assertIn(frame.function_name, (function_name, function), f"Unexpected frame: {frame.function_name}")
            self.assertEqual(len(frame.locals), 1, f"Unexpected locals for {function_name}")
            if struct_format.startswith("<"):
                self.assert_variable(frame.locals[0], "reg_value", value, True, f"reg_value of {function_name}")
            else:
                # A const char* held in a callee-saved register: verify it points at the test string.
                address = self.get_symbol_address(parsed_elf, struct_format)
                self.assert_string_pointer(frame.locals[0], "reg_value", address, f"reg_value of {function_name}")

    @parameterized.expand(
        [
            ("abcd", "build/riscv-src/blackhole/callstack.debug.brisc.elf"),  # Invalid location string
            ("0,0", "invalid_elf_path"),  # Invalid elf path
            (
                "0,0",
                ["build/riscv-src/blackhole/callstack.debug.brisc.elf", "invalid_elf_path"],
            ),  # One of elf paths is invalid
            (
                "0,0",
                ["build/riscv-src/blackhole/callstack.debug.brisc.elf"],
                [0, 1],
            ),  # Length of elf_paths and offsets is different
            ("0,0", "build/riscv-src/blackhole/callstack.debug.brisc.elf", 0, "invalid"),  # Invalid risc_name
            (
                "0,0",
                "build/riscv-src/blackhole/callstack.debug.brisc.elf",
                0,
                "brisc",
                -1,
            ),  # Invalid max_depth (too low)
            ("0,0", "build/riscv-src/blackhole/callstack.debug.brisc.elf", 0, "brisc", 1, -1),  # Invalid device_id
        ]
    )
    def test_callstack_invalid(self, location, elf_paths, offsets=None, risc_name="brisc", max_depth=100, device_id=0):
        """Test invalid inputs for callstack function."""

        # Check for invalid location
        with self.assertRaises((TTException, ValueError, FileNotFoundError)):
            lib.callstack(location, elf_paths, offsets, risc_name, None, max_depth, True, device_id, self.context)
