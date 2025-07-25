# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import struct
import unittest
import os

from functools import wraps

from parameterized import parameterized, parameterized_class

from test.ttexalens.unit_tests.test_base import init_default_test_context
from ttexalens import tt_exalens_init
from ttexalens import tt_exalens_lib as lib
from ttexalens import util

from ttexalens.coordinate import OnChipCoordinate
from ttexalens.context import Context
from ttexalens.device import Device
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription
from ttexalens.firmware import ELF
from ttexalens.hardware.baby_risc_debug import BabyRiscDebug
from ttexalens.hardware.risc_debug import CallstackEntry, RiscDebug
from ttexalens.object import DataArray

from ttexalens.hw.arc.arc import load_arc_fw
from ttexalens.hw.arc.arc_dbg_fw import arc_dbg_fw_check_msg_loop_running, arc_dbg_fw_command, NUM_LOG_CALLS_OFFSET
from ttexalens.register_store import ConfigurationRegisterDescription, DebugRegisterDescription
from ttexalens.elf_loader import ElfLoader


def invalid_argument_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        return func(*args, **kwargs)

    return wrapper


class TestAutoContext(unittest.TestCase):
    def test_auto_context(self):
        """Test auto context creation."""
        tt_exalens_init.GLOBAL_CONTEXT = None
        context = lib.check_context()
        self.assertIsNotNone(context)
        self.assertIsInstance(context, Context)

    def test_set_global_context(self):
        """Test setting global context."""
        tt_exalens_init.GLOBAL_CONTEXT = None
        context = tt_exalens_init.init_ttexalens()
        self.assertIsNotNone(tt_exalens_init.GLOBAL_CONTEXT)
        self.assertIs(tt_exalens_init.GLOBAL_CONTEXT, context)

    def test_existing_context(self):
        """Test recognition of existing context."""
        tt_exalens_init.GLOBAL_CONTEXT = None

        # Create new global context
        context1 = tt_exalens_init.init_ttexalens()
        self.assertIsNotNone(tt_exalens_init.GLOBAL_CONTEXT)
        self.assertIs(tt_exalens_init.GLOBAL_CONTEXT, context1)

        # Check for existing context
        context = lib.check_context()
        self.assertIsNotNone(context)
        self.assertIs(tt_exalens_init.GLOBAL_CONTEXT, context)
        self.assertIs(context, context1)


class TestReadWrite(unittest.TestCase):
    def setUp(self):
        self.context = init_default_test_context()
        self.assertIsNotNone(self.context)
        self.assertIsInstance(self.context, Context)

    def test_write_read(self):
        """Test write data -- read data."""
        core_loc = "0,0"
        address = 0x100

        data = [0, 1, 2, 3]

        ret = lib.write_to_device(core_loc, address, data)
        self.assertEqual(ret, len(data))

        ret = lib.read_from_device(core_loc, address, num_bytes=len(data))
        self.assertEqual(ret, bytes(data))

    def test_write_read_bytes(self):
        """Test write bytes -- read bytes."""
        core_loc = "1,0"
        address = 0x100

        data = b"abcd"

        ret = lib.write_to_device(core_loc, address, data)
        self.assertEqual(ret, len(data))

        ret = lib.read_from_device(core_loc, address, num_bytes=len(data))
        self.assertEqual(ret, data)

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
    def test_write_read_bytes_buffer(self, core_loc: str, size: int, address: int, device_id: int):
        """Test write bytes -- read bytes but with bigger buffer."""

        if device_id >= len(self.context.devices):
            self.skipTest("Device ID out of range.")

        # Create buffer
        data = bytes([i % 256 for i in range(size)])
        words = [int.from_bytes(data[i : i + 4], byteorder="little") for i in range(0, len(data), 4)]

        # Write buffer
        ret = lib.write_to_device(core_loc, address, data, device_id)
        self.assertEqual(ret, len(data))

        # Verify buffer as words
        ret = lib.read_words_from_device(core_loc, address, device_id, len(words))
        self.assertEqual(ret, words)

        # Write words
        lib.write_words_to_device(core_loc, address, words, device_id)

        # Read buffer
        ret = lib.read_from_device(core_loc, address, device_id, num_bytes=len(data))
        self.assertEqual(ret, data)

    def test_write_read_words(self):
        """Test write words -- read words."""
        core_loc = "1,0"

        address = [0x100, 0x104, 0x108]
        data = [156, 2, 212, 9]

        # Write a word to device two times
        ret = lib.write_words_to_device(core_loc, address[0], data[0])
        self.assertEqual(ret, 4)

        ret = lib.write_words_to_device(core_loc, address[1], data[1])
        self.assertEqual(ret, 4)

        # Write two words to device
        ret = lib.write_words_to_device(core_loc, address[2], data[2:])

        # Read the first word
        ret = lib.read_words_from_device(core_loc, address[0])
        self.assertEqual(ret[0], data[0])

        # Read the second word
        ret = lib.read_words_from_device(core_loc, address[1])
        self.assertEqual(ret[0], data[1])

        # Read first two words
        ret = lib.read_words_from_device(core_loc, address[0], word_count=2)
        self.assertEqual(ret, data[0:2])

        # Read third and fourth words
        ret = lib.read_words_from_device(core_loc, address[2], word_count=2)
        self.assertEqual(ret, data[2:])

    def test_write_bytes_read_words(self):
        """Test write bytes -- read words."""
        core_loc = "1,0"
        address = 0x100
        data = [0, 1, 2, 3]

        # Write bytes to device
        ret = lib.write_to_device(core_loc, address, data)
        # *4 is because we write 4-byte words
        self.assertEqual(ret, len(data))

        # Read the bytes as words
        ret = lib.read_words_from_device(core_loc, address, word_count=1)
        self.assertEqual(ret[0].to_bytes(4, "little"), bytes(data))

    @parameterized.expand(
        [
            ("abcd", 0x100, 0, 1),  # Invalid core_loc string
            ("-10", 0x100, 0, 1),  # Invalid core_loc string
            ("0,0", -1, 0, 1),  # Invalid address
            ("0,0", 0x100, -1, 1),  # Invalid device_id
            ("0,0", 0x100, 112, 1),  # Invalid device_id (too high)
            ("0,0", 0x100, 0, -1),  # Invalid word_count
            ("0,0", 0x100, 0, 0),  # Invalid word_count
        ]
    )
    def test_invalid_inputs_read(self, core_loc, address, device_id, word_count):
        """Test invalid inputs for read functions."""
        with self.assertRaises((util.TTException, ValueError)):
            lib.read_words_from_device(core_loc, address, device_id, word_count)
        with self.assertRaises((util.TTException, ValueError)):
            # word_count can be used as num_bytes
            lib.read_from_device(core_loc, address, device_id, word_count)

    @parameterized.expand(
        [
            ("abcd", 0x100, 5, 0),  # Invalid core_loc string
            ("-10", 0x100, 5, 0),  # Invalid core_loc string
            ("0,0", -1, 5, 0),  # Invalid address
            ("0,0", 0x100, 5, -1),  # Invalid device_id
            ("0,0", 0x100, 5, 112),  # Invalid device_id (too high)
            # ("0,0", 0x100, -171, -1),        # Invalid word TODO: What are the limits for word?
        ]
    )
    def test_invalid_write_word(self, core_loc, address, data, device_id):
        with self.assertRaises((util.TTException, ValueError)):
            lib.write_words_to_device(core_loc, address, data, device_id)

    @parameterized.expand(
        [
            ("abcd", 0x100, b"abcd", 0),  # Invalid core_loc string
            ("-10", 0x100, b"abcd", 0),  # Invalid core_loc string
            ("0,0", -1, b"abcd", 0),  # Invalid address
            ("0,0", 0x100, b"abcd", -1),  # Invalid device_id
            ("0,0", 0x100, b"abcd", 112),  # Invalid device_id (too high)
            ("0,0", 0x100, [], 0),  # Invalid data
            ("0,0", 0x100, b"", 0),  # Invalid data
        ]
    )
    def test_invalid_write(self, core_loc, address, data, device_id):
        """Test invalid inputs for write function."""
        with self.assertRaises((util.TTException, ValueError)):
            lib.write_to_device(core_loc, address, data, device_id)

    def test_unaligned_read(self):
        for device_id in self.context.device_ids:
            core_loc = self.context.devices[device_id].get_block_locations()[0]
            lib.write_words_to_device(core_loc, 0, [0x12345678, 0x90ABCDEF], device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x12345678, 0x90ABCDEF]
            assert lib.read_from_device(core_loc, 0, device_id, 1, self.context) == bytes([0x78])
            assert lib.read_from_device(core_loc, 1, device_id, 1, self.context) == bytes([0x56])
            assert lib.read_from_device(core_loc, 2, device_id, 1, self.context) == bytes([0x34])
            assert lib.read_from_device(core_loc, 3, device_id, 1, self.context) == bytes([0x12])
            assert lib.read_from_device(core_loc, 4, device_id, 1, self.context) == bytes([0xEF])
            assert lib.read_from_device(core_loc, 5, device_id, 1, self.context) == bytes([0xCD])
            assert lib.read_from_device(core_loc, 6, device_id, 1, self.context) == bytes([0xAB])
            assert lib.read_from_device(core_loc, 7, device_id, 1, self.context) == bytes([0x90])
            assert lib.read_from_device(core_loc, 0, device_id, 2, self.context) == bytes([0x78, 0x56])
            assert lib.read_from_device(core_loc, 2, device_id, 2, self.context) == bytes([0x34, 0x12])
            assert lib.read_from_device(core_loc, 4, device_id, 2, self.context) == bytes([0xEF, 0xCD])
            assert lib.read_from_device(core_loc, 6, device_id, 2, self.context) == bytes([0xAB, 0x90])
            assert lib.read_from_device(core_loc, 0, device_id, 4, self.context) == bytes([0x78, 0x56, 0x34, 0x12])
            assert lib.read_from_device(core_loc, 4, device_id, 4, self.context) == bytes([0xEF, 0xCD, 0xAB, 0x90])
            assert lib.read_from_device(core_loc, 0, device_id, 8, self.context) == bytes(
                [0x78, 0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB, 0x90]
            )
            assert lib.read_from_device(core_loc, 1, device_id, 2, self.context) == bytes([0x56, 0x34])
            assert lib.read_from_device(core_loc, 3, device_id, 2, self.context) == bytes([0x12, 0xEF])
            assert lib.read_from_device(core_loc, 5, device_id, 2, self.context) == bytes([0xCD, 0xAB])
            assert lib.read_from_device(core_loc, 1, device_id, 4, self.context) == bytes([0x56, 0x34, 0x12, 0xEF])
            assert lib.read_from_device(core_loc, 2, device_id, 4, self.context) == bytes([0x34, 0x12, 0xEF, 0xCD])
            assert lib.read_from_device(core_loc, 3, device_id, 4, self.context) == bytes([0x12, 0xEF, 0xCD, 0xAB])
            assert lib.read_from_device(core_loc, 0, device_id, 8, self.context) == bytes(
                [0x78, 0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB, 0x90]
            )
            assert lib.read_from_device(core_loc, 1, device_id, 6, self.context) == bytes(
                [0x56, 0x34, 0x12, 0xEF, 0xCD, 0xAB]
            )

    def test_unaligned_write(self):
        for device_id in self.context.device_ids:
            core_loc = self.context.devices[device_id].get_block_locations()[0]
            lib.write_words_to_device(core_loc, 0, [0xDEADBEEF, 0xDEADBEEF], device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0xDEADBEEF, 0xDEADBEEF]
            lib.write_to_device(core_loc, 0, bytes([0x12]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0xDEADBE12, 0xDEADBEEF]
            lib.write_to_device(core_loc, 1, bytes([0x34]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0xDEAD3412, 0xDEADBEEF]
            lib.write_to_device(core_loc, 2, bytes([0x56]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0xDE563412, 0xDEADBEEF]
            lib.write_to_device(core_loc, 3, bytes([0x78]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x78563412, 0xDEADBEEF]
            lib.write_to_device(core_loc, 4, bytes([0x90]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x78563412, 0xDEADBE90]
            lib.write_to_device(core_loc, 5, bytes([0xAB]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x78563412, 0xDEADAB90]
            lib.write_to_device(core_loc, 6, bytes([0xCD]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x78563412, 0xDECDAB90]
            lib.write_to_device(core_loc, 7, bytes([0xEF]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x78563412, 0xEFCDAB90]
            lib.write_to_device(core_loc, 0, bytes([0xAA, 0xBB]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x7856BBAA, 0xEFCDAB90]
            lib.write_to_device(core_loc, 2, bytes([0xCC, 0xDD]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0xDDCCBBAA, 0xEFCDAB90]
            lib.write_to_device(core_loc, 4, bytes([0xEE, 0xFF]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0xDDCCBBAA, 0xEFCDFFEE]
            lib.write_to_device(core_loc, 6, bytes([0x00, 0x11]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0xDDCCBBAA, 0x1100FFEE]
            lib.write_to_device(core_loc, 1, bytes([0x22, 0x33]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0xDD3322AA, 0x1100FFEE]
            lib.write_to_device(core_loc, 3, bytes([0x44, 0x55]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x443322AA, 0x1100FF55]
            lib.write_to_device(core_loc, 5, bytes([0x66, 0x77]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x443322AA, 0x11776655]
            lib.write_to_device(core_loc, 2, bytes([0x88, 0x99, 0xAA]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x998822AA, 0x117766AA]
            lib.write_to_device(core_loc, 3, bytes([0xBB, 0xCC, 0xDD]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0xBB8822AA, 0x1177DDCC]
            lib.write_to_device(core_loc, 1, bytes([0x11, 0x22, 0x33, 0x44, 0x55, 0x66]), device_id, self.context)
            assert lib.read_words_from_device(core_loc, 0, device_id, 2, self.context) == [0x332211AA, 0x11665544]

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
        ]
    )
    def test_write_read_tensix_register(self, core_loc, register, value):
        """Test writing and reading tensix registers"""
        if self.context.arch == "grayskull":
            self.skipTest("Skipping the test on grayskull.")

        # Storing the original value of the register
        original_value = lib.read_tensix_register(core_loc, register)

        # Writing a value to the register and reading it back
        lib.write_tensix_register(core_loc, register, value)
        ret = lib.read_tensix_register(core_loc, register)

        # Checking if the value was written and read correctly
        self.assertEqual(ret, value)

        # Writing the original value back to the register and reading it
        lib.write_tensix_register(core_loc, register, original_value)
        ret = lib.read_tensix_register(core_loc, register)

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
    def test_write_read_tensix_register_with_name(self, core_loc, register_description, register_name):
        "Test writing and reading tensix registers with name"
        if self.context.arch == "grayskull":
            self.skipTest("Skipping the test on grayskull.")

        # Reading original values of registers
        original_val_desc = lib.read_tensix_register(core_loc, register_description)
        original_val_name = lib.read_tensix_register(core_loc, register_name)

        # Checking if values are equal
        self.assertEqual(original_val_desc, original_val_name)

        # Writing a value to the register given by description
        lib.write_tensix_register(core_loc, register_description, 1)

        # Reading values from both registers
        val_desc = lib.read_tensix_register(core_loc, register_description)
        val_name = lib.read_tensix_register(core_loc, register_name)

        # Checking if writing to description register affects the name register (making sure they are the same)
        self.assertEqual(val_desc, val_name)

        # Wrting original value back
        lib.write_tensix_register(core_loc, register_name, original_val_name)

        val_desc = lib.read_tensix_register(core_loc, register_description)
        val_name = lib.read_tensix_register(core_loc, register_name)

        # Checking if original values are restored
        self.assertEqual(val_name, original_val_name)
        self.assertEqual(val_desc, original_val_desc)

    @parameterized.expand(
        [
            ("abcd", ConfigurationRegisterDescription(), 0, 0),  # Invalid core_loc string
            ("-10", ConfigurationRegisterDescription(), 0, 0),  # Invalid core_loc string
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
    def test_invalid_write_read_tensix_register(self, core_loc, register, value, device_id):
        """Test invalid inputs for tensix register read and write functions."""
        if self.context.arch == "grayskull":
            self.skipTest("Skipping the test on grayskull.")

        if value == 0:  # Invalid value does not raies an exception in read so we skip it
            with self.assertRaises((util.TTException, ValueError)):
                lib.read_tensix_register(core_loc, register, device_id)
        with self.assertRaises((util.TTException, ValueError)):
            lib.write_tensix_register(core_loc, register, value, device_id)

    def write_program(self, core_loc, addr, data):
        """Write program code data to L1 memory."""
        bytes_written = lib.write_words_to_device(core_loc, addr, data, context=self.context)
        self.assertEqual(bytes_written, 4)

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
            ("0,0", "trisc0", -1),  # last address for trisc for wormhole
            ("0,0", "brisc", -1),  # last address for brisc for wormhole
        ]
    )
    def test_write_read_private_memory(self, core_loc: str, risc_name: str, addr: int | None = None):
        """Testing read_memory and write_memory through debugging interface on private core memory range."""

        loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
        risc_debug = loc._device.get_block(loc).get_risc_debug(risc_name)

        if risc_debug.risc_info.can_change_code_start_address:
            risc_debug.risc_info.set_code_start_address(risc_debug.register_store, 0xD000)

        if addr is None or addr < 0:
            private_memory = risc_debug.get_data_private_memory()
            assert private_memory is not None, "Private memory is not available."
            assert private_memory.address.private_address is not None, "Private memory address is not set."
            if addr is None:
                addr = private_memory.address.private_address
            else:
                addr = private_memory.address.private_address + private_memory.size - 4

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
            ("abcd", 0xFFB00000, 0),  # Invalid core_loc string
            ("-10", 0xFFB00000, 0),  # Invalid core_loc string
            ("0,0", 0xFFA00000, 0),  # Invalid address (too low)
            ("0,0", 0xFFC00000, 0),  # Invalid address (too high)
            ("0,0", 0xFFB00000, 0, "invalid"),  # Invalid risc_name
            ("0,0", 0xFFB00000, 0, "brisc", -1),  # Invalid device_id
            ("0,0", 0xFFB00000, 0, "brisc", 2**32),  # Invalid device_id
        ]
    )
    def test_invalid_read_private_memory(self, core_loc: str, address: int, value: int, risc_name="brisc", device_id=0):
        """Test invalid inputs for reading private memory."""
        if value == 0:  # Invalid value does not raies an exception in read so we skip it
            with self.assertRaises((util.TTException, ValueError)):
                lib.read_riscv_memory(core_loc, address, risc_name, None, device_id)
        with self.assertRaises((util.TTException, ValueError)):
            lib.write_riscv_memory(core_loc, address, value, risc_name, None, device_id)


class TestRunElf(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = init_default_test_context()

    def is_blackhole(self):
        """Check if the device is blackhole."""
        return self.context.devices[0]._arch == "blackhole"

    def get_elf_path(self, app_name: str, risc_name: str):
        """Get the path to the ELF file."""
        arch = self.context.devices[0]._arch.lower()
        if arch == "wormhole_b0":
            arch = "wormhole"
        risc = risc_name.lower()
        return f"build/riscv-src/{arch}/{app_name}.{risc}.elf"

    @parameterized.expand(
        [
            ("brisc"),
            ("trisc0"),
            ("trisc1"),
            ("trisc2"),
            ("ncrisc"),
        ]
    )
    def test_run_elf(self, risc_name: str):
        """Test running an ELF file."""
        core_loc = "0,0"
        addr = 0x0

        # Reset memory at addr
        lib.write_words_to_device(core_loc, addr, 0, context=self.context)
        ret = lib.read_words_from_device(core_loc, addr, context=self.context)
        self.assertEqual(ret[0], 0)

        # Run an ELF that writes to the addr and check if it executed correctly
        elf_path = self.get_elf_path("run_elf_test", risc_name)
        lib.run_elf(elf_path, core_loc, risc_name, context=self.context)
        ret = lib.read_words_from_device(core_loc, addr, context=self.context)
        self.assertEqual(ret[0], 0x12345678)

    @parameterized.expand(
        [
            ("", "0,0", "brisc", 0),  # Invalid ELF path
            ("/sbin/non_existing_elf", "0,0", "brisc", 0),  # Invalid ELF path
            (None, "abcd", "brisc", 0),  # Invalid core_loc
            (None, "-10", "brisc", 0),  # Invalid core_loc
            (None, "0,0/", "brisc", 0),  # Invalid core_loc
            (None, "0,0/00b", "brisc", 0),  # Invalid core_loc
            (None, "0,0", "invalid", 0),  # Invalid risc_name
            (None, "0,0", "brisc", -1),  # Invalid device_id
            (None, "0,0", "brisc", 112),  # Invalid device_id (too high)
        ]
    )
    def test_run_elf_invalid(self, elf_file, core_loc, risc_name, device_id):
        if elf_file is None:
            elf_file = self.get_elf_path("run_elf_test", "brisc")
        with self.assertRaises((util.TTException, ValueError)):
            lib.run_elf(elf_file, core_loc, risc_name, None, device_id, context=self.context)

    @parameterized.expand(
        [
            ("brisc"),
            ("trisc0"),
            ("trisc1"),
            ("trisc2"),
        ]
    )
    def test_old_elf_test(self, risc_name: str):
        if self.is_blackhole():
            self.skipTest("This test doesn't work as expected on blackhole. Disabling it until bug #120 is fixed.")

        """ Running old elf test, formerly done with -t option. """
        core_loc = "0,0"
        elf_path = self.get_elf_path("sample", risc_name)

        lib.run_elf(elf_path, core_loc, risc_name, context=self.context)

        # Testing
        elf = ELF(self.context.server_ifc, {"fw": elf_path})
        MAILBOX_ADDR, MAILBOX_SIZE, _, _ = elf.parse_addr_size_value_type("fw.g_MAILBOX")
        TESTBYTEACCESS_ADDR, _, _, _ = elf.parse_addr_size_value_type("fw.g_TESTBYTEACCESS")

        loc = OnChipCoordinate.create(core_loc, device=self.context.devices[0])
        device = loc._device
        noc_block = device.get_block(loc)
        risc_debug = noc_block.get_risc_debug(risc_name)
        assert isinstance(risc_debug, BabyRiscDebug), f"Expected BabyRiscDebug, got {type(risc_debug)}"
        rdbg: BabyRiscDebug = risc_debug
        assert rdbg.debug_hardware is not None, "Debug hardware is not available."
        rloader = ElfLoader(rdbg)

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
        mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE)
        da = DataArray("g_MAILBOX")
        mbox_val = da.from_bytes(mbox_val)[0]
        self.assertEqual(mbox_val, 0xFFB1208C, f"RISC at location {loc} did not set the mailbox value to 0xFFB1208C.")
        # TODO: Add this back in once we get a library version: gpr_command["module"].run("gpr pc,sp", context, ui_state)

        # Step 2: Write 0x1234 to the mailbox to resume operation.
        try:
            da.data = [0x1234]
            bts = da.bytes()
            rloader.write_block(MAILBOX_ADDR, bts)
        except Exception as e:
            if e.args[0].startswith("Failed to continue"):
                # We are expecting this to assert as here, the core will halt istself by calling halt()
                pass
            else:
                raise e

        # Step 3: Check that the RISC at location {loc} set the mailbox value to 0xFFB12080.
        mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE)
        da = DataArray("g_MAILBOX")
        mbox_val = da.from_bytes(mbox_val)[0]
        self.assertEqual(mbox_val, 0xFFB12080, f"RISC at location {loc} did not set the mailbox value to 0xFFB12080.")

        # Step 4: Check that the RISC at location {loc} is halted.
        status = rdbg.debug_hardware.read_status()
        # print_PC_and_source(rdbg.read_gpr(32), elf)
        self.assertTrue(status.is_halted, f"Step 4: RISC at location {loc} is not halted.")
        self.assertTrue(status.is_ebreak_hit, f"Step 4: RISC at location {loc} is not halted with ebreak.")

        # Step 5a: Make sure that the core did not reach step 5
        mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE)
        da = DataArray("g_MAILBOX")
        mbox_val = da.from_bytes(mbox_val)[0]
        self.assertNotEqual(mbox_val, 0xFFB12088, f"RISC at location {loc} reached step 5, but it should not have.")

        # Step 5b: Continue and check that the core reached 0xFFB12088. But first set the breakpoint at
        # function "decrement_mailbox"
        decrement_mailbox_die = elf.names["fw"].subprograms["decrement_mailbox"]
        decrement_mailbox_linkage_name = decrement_mailbox_die.attributes["DW_AT_linkage_name"].value.decode("utf-8")
        decrement_mailbox_address = elf.names["fw"].symbols[decrement_mailbox_linkage_name].value

        # Step 6. Setting breakpoint at decrement_mailbox
        watchpoint_id = 1  # Out of 8
        rdbg.debug_hardware.set_watchpoint_on_pc_address(watchpoint_id, decrement_mailbox_address)
        rdbg.debug_hardware.set_watchpoint_on_memory_write(
            0, TESTBYTEACCESS_ADDR
        )  # Set memory watchpoint on TESTBYTEACCESS
        rdbg.debug_hardware.set_watchpoint_on_memory_write(3, TESTBYTEACCESS_ADDR + 3)
        rdbg.debug_hardware.set_watchpoint_on_memory_write(4, TESTBYTEACCESS_ADDR + 4)
        rdbg.debug_hardware.set_watchpoint_on_memory_write(5, TESTBYTEACCESS_ADDR + 5)

        mbox_val = 1
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
            mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE)
            da = DataArray("g_MAILBOX")
            mbox_val = da.from_bytes(mbox_val)[0]
            # Step 5b: Continue RISC
            timeout_retries -= 1

        if timeout_retries == 0 and mbox_val != 0:
            raise util.TTFatalException(f"RISC at location {loc} did not get past step 6.")
        self.assertFalse(
            rdbg.debug_hardware.is_pc_watchpoint_hit(),
            f"RISC at location {loc} hit the breakpoint but it should not have.",
        )

        # STEP 7: Testing byte access memory watchpoints")
        mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE)
        da = DataArray("g_MAILBOX")
        mbox_val = da.from_bytes(mbox_val)[0]
        self.assertEqual(mbox_val, 0xFF000003, f"RISC at location {loc} did not set the mailbox value to 0xff000003.")
        status = rdbg.debug_hardware.read_status()
        self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
        if not status.is_memory_watchpoint_hit or not status.watchpoints_hit[3]:
            raise util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 3.")
        rdbg.cont()

        mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE)
        da = DataArray("g_MAILBOX")
        mbox_val = da.from_bytes(mbox_val)[0]
        self.assertEqual(mbox_val, 0xFF000005, f"RISC at location {loc} did not set the mailbox value to 0xff000005.")
        status = rdbg.debug_hardware.read_status()
        self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
        if not status.is_memory_watchpoint_hit or not status.watchpoints_hit[5]:
            raise util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 5.")
        rdbg.cont()

        mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE)
        da = DataArray("g_MAILBOX")
        mbox_val = da.from_bytes(mbox_val)[0]
        self.assertEqual(mbox_val, 0xFF000000, f"RISC at location {loc} did not set the mailbox value to 0xff000000.")
        status = rdbg.debug_hardware.read_status()
        self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
        if not status.is_memory_watchpoint_hit or not status.watchpoints_hit[0]:
            raise util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 0.")
            return False
        rdbg.cont()

        mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE)
        da = DataArray("g_MAILBOX")
        mbox_val = da.from_bytes(mbox_val)[0]
        self.assertEqual(mbox_val, 0xFF000004, f"RISC at location {loc} did not set the mailbox value to 0xff000004.")
        status = rdbg.debug_hardware.read_status()
        self.assertTrue(status.is_halted, f"Step 7: RISC at location {loc} is not halted.")
        if not status.is_memory_watchpoint_hit or not status.watchpoints_hit[4]:
            raise util.TTFatalException(f"Step 7: RISC at location {loc} is not halted with memory watchpoint 4.")
        rdbg.cont()

        # STEP END:
        mbox_val = rloader.read_block(MAILBOX_ADDR, MAILBOX_SIZE)
        da = DataArray("g_MAILBOX")
        mbox_val = da.from_bytes(mbox_val)[0]
        self.assertEqual(mbox_val, 0xFFB12088, f"RISC at location {loc} did not reach step STEP END.")

        # Enable branch prediction
        rdbg.set_branch_prediction(True)


class TestARC(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = tt_exalens_init.init_ttexalens()

    def is_wormhole(self):
        """Check if the device is wormhole."""
        return self.context.devices[0]._arch == "wormhole_b0"

    def is_blackhole(self):
        """Check if the device is blackhole."""
        return self.context.devices[0]._arch == "blackhole"

    def test_arc_msg(self):
        """Test getting AICLK from ARC."""

        if self.is_blackhole():
            self.skipTest("Arc message is not supported on blackhole UMD")

        device_id = 0
        msg_code = 0x90  # ArcMessageType::TEST
        wait_for_done = True
        arg0 = 0
        arg1 = 0
        timeout = 1000

        # Ask for reply, check for reasonable TEST value
        ret, return_3, _ = lib.arc_msg(device_id, msg_code, wait_for_done, arg0, arg1, timeout, context=self.context)

        print(f"ARC message result={ret}, test={return_3}")
        self.assertEqual(ret, 0)

        # Asserting that return_3 (test) is 0
        self.assertEqual(return_3, 0)

    fw_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../..", "fw/arc/arc_bebaceca.hex")

    def test_read_arc_telemetry(self):
        """Test reading ARC telemetry entries of known values"""
        device_id = 0
        if self.is_wormhole():
            # Check vendor ID
            expected_vendor_id = 0x1E52
            vendor_id = lib.read_arc_telemetry_entry(device_id, "TAG_DEVICE_ID") & 0xFFFF
            self.assertEqual(vendor_id, expected_vendor_id)

            # Check if heartbeat is increasing
            import time

            heartbeat1 = lib.read_arc_telemetry_entry(device_id, "TAG_ARC0_HEALTH")
            time.sleep(0.1)
            heartbeat2 = lib.read_arc_telemetry_entry(device_id, "TAG_ARC0_HEALTH")
            self.assertGreater(heartbeat2, heartbeat1)
        elif self.is_blackhole():
            # Check if heartbeat is increasing
            import time

            heartbeat1 = lib.read_arc_telemetry_entry(device_id, "TAG_TIMER_HEARTBEAT")
            time.sleep(0.1)
            heartbeat2 = lib.read_arc_telemetry_entry(device_id, "TAG_TIMER_HEARTBEAT")
            self.assertGreater(heartbeat2, heartbeat1)
        else:
            self.skipTest("ARC telemetry is not supported for this architecture")

    @parameterized.expand(
        [
            ("TAG_BOARD_ID_HIGH", (4, 1)),
            ("TAG_BOARD_ID_LOW", (5, 2)),
            ("TAG_AICLK", (24, 14)),
            ("TAG_AXICLK", (25, 15)),
            ("TAG_ARCCLK", (26, 16)),
        ]
    )
    def test_read_arc_telemetry_entry(self, tag_name, tag_id):
        """Test reading ARC telemetry entry by tag name and tag ID"""

        index = 0 if self.is_wormhole() else 1 if self.is_blackhole() else None

        if index is None:
            self.skipTest("ARC telemetry is not supported for this architecture")

        device_id = 0

        # Check if reading by tag name and tag ID gives the same result
        ret_from_name = lib.read_arc_telemetry_entry(device_id, tag_name)
        ret_from_id = lib.read_arc_telemetry_entry(device_id, tag_id[index])
        self.assertEqual(ret_from_name, ret_from_id)

    def test_load_arc_fw(self):

        if self.is_blackhole():
            self.skipTest("Loading ARC firmware is not supported on blackhole")

        wait_time = 0.1
        TT_METAL_ARC_DEBUG_BUFFER_SIZE = 1024

        for device_id in self.context.device_ids:
            load_arc_fw(self.fw_file_path, 2, device_id, context=self.context)
            device = self.context.devices[device_id]
            arc = device.arc_block
            scratch2 = arc.get_register_store().read_register("ARC_RESET_SCRATCH2")
            assert scratch2 == 0xBEBACECA


@parameterized_class(
    [
        {"core_desc": "ETH0", "risc_name": "ERISC"},
        {"core_desc": "ETH0", "risc_name": "ERISC0"},
        {"core_desc": "ETH0", "risc_name": "ERISC1"},
        {"core_desc": "FW0", "risc_name": "BRISC"},
        {"core_desc": "FW0", "risc_name": "TRISC0"},
        {"core_desc": "FW0", "risc_name": "TRISC1"},
        # {"core_desc": "FW0", "risc_name": "TRISC2"}, - there is a bug on TRISC2: #266
    ]
)
class TestCallStack(unittest.TestCase):
    risc_name: str  # Risc name
    risc_id: int  # Risc ID - being parametrized
    context: Context  # TTExaLens context
    core_desc: str  # Core description ETH0, FW0, FW1 - being parametrized
    core_loc: str  # Core location
    location: OnChipCoordinate  # Core location
    risc_debug: RiscDebug  # RiscDebug object
    loader: ElfLoader  # ElfLoader object
    pc_register_index: int  # PC register index
    device: Device  # Device

    @classmethod
    def setUpClass(cls):
        cls.context = tt_exalens_init.init_ttexalens()

    def setUp(self):
        self.device = self.context.devices[0]
        # Convert core_desc to core_loc
        if self.core_desc.startswith("ETH"):
            # Ask device for all ETH cores and get first one
            eth_cores = self.device.get_block_locations(block_type="eth")
            core_index = int(self.core_desc[3:])
            if len(eth_cores) > core_index:
                self.core_loc = eth_cores[core_index].to_str()
            else:
                # If not found, we should skip the test
                self.skipTest("ETH core is not available on this platform")
        elif self.core_desc.startswith("FW"):
            # Ask device for all ETH cores and get first one
            eth_cores = self.device.get_block_locations(block_type="functional_workers")
            core_index = int(self.core_desc[2:])
            if len(eth_cores) > core_index:
                self.core_loc = eth_cores[core_index].to_str()
            else:
                # If not found, we should skip the test
                self.skipTest("FW core is not available on this platform")
        else:
            self.fail(f"Unknown core description {self.core_desc}")

        self.location = OnChipCoordinate.create(self.core_loc, device=self.device)
        noc_block = self.location._device.get_block(self.location)
        try:
            self.risc_debug = noc_block.get_risc_debug(self.risc_name)
        except ValueError as e:
            self.skipTest(f"{self.risc_name} core is not available in this block on this platform")

        self.loader = ElfLoader(self.risc_debug)

        # Stop risc with reset
        self.risc_debug.set_reset_signal(True)
        self.assertTrue(self.risc_debug.is_in_reset())

    def tearDown(self):
        # Stop risc with reset
        self.risc_debug.set_reset_signal(True)
        self.assertTrue(self.risc_debug.is_in_reset())

    def is_wormhole(self):
        """Check if the device is wormhole"""
        return self.device._arch == "wormhole_b0"

    def is_blackhole(self):
        """Check if the device is blackhole."""
        return self.device._arch == "blackhole"

    def is_eth_block(self):
        """Check if the core is ETH."""
        return self.device.get_block_type(self.location) == "eth"

    def get_elf_path(self, app_name):
        """Get the path to the ELF file."""
        arch = self.device._arch.lower()
        if arch == "wormhole_b0":
            arch = "wormhole"
        if self.risc_name.lower().startswith("erisc"):
            # For eriscs we can use brisc elf
            return f"build/riscv-src/{arch}/{app_name}.brisc.elf"
        else:
            return f"build/riscv-src/{arch}/{app_name}.{self.risc_name.lower()}.elf"

    @parameterized.expand([1, 10, 50])
    def test_callstack_with_parsing(self, recursion_count):
        self.is_wormhole()
        lib.write_words_to_device(self.core_loc, 0x4000, recursion_count, 0, self.context)
        elf_path = self.get_elf_path("callstack")
        self.loader.run_elf(elf_path)
        parsed_elf = lib.parse_elf(elf_path, self.context)
        callstack: list[CallstackEntry] = lib.callstack(
            self.core_loc, parsed_elf, None, self.risc_name, None, 100, True, False, 0, self.context
        )
        self.assertEqual(len(callstack), recursion_count + 3)
        self.assertEqual(callstack[0].function_name, "halt")
        for i in range(1, recursion_count + 1):
            self.assertEqual(callstack[i].function_name, "f1")
        self.assertEqual(callstack[recursion_count + 1].function_name, "recurse")
        self.assertEqual(callstack[recursion_count + 2].function_name, "main")

    @parameterized.expand([1, 10, 50])
    def test_callstack(self, recursion_count: int):
        lib.write_words_to_device(self.core_loc, 0x4000, recursion_count, 0, self.context)
        elf_path = self.get_elf_path("callstack")
        self.loader.run_elf(elf_path)
        callstack: list[CallstackEntry] = lib.callstack(
            self.core_loc, elf_path, None, self.risc_name, None, 100, True, False, 0, self.context
        )
        self.assertEqual(len(callstack), recursion_count + 3)
        self.assertEqual(callstack[0].function_name, "halt")
        for i in range(1, recursion_count + 1):
            self.assertEqual(callstack[i].function_name, "f1")
        self.assertEqual(callstack[recursion_count + 1].function_name, "recurse")
        self.assertEqual(callstack[recursion_count + 2].function_name, "main")

    @parameterized.expand(["callstack", "callstack.optimized"])
    def test_callstack_namespace(self, elf_name):

        if self.is_wormhole() and self.is_eth_block() and elf_name == "callstack.optimized":
            self.skipTest("Callstack optimized tests break on ETH blocks")

        lib.write_words_to_device(self.core_loc, 0x4000, 0, 0, self.context)
        elf_path = self.get_elf_path(elf_name)
        self.loader.run_elf(elf_path)
        callstack: list[CallstackEntry] = lib.callstack(
            self.core_loc, elf_path, None, self.risc_name, None, 100, True, False, 0, self.context
        )
        self.assertEqual(len(callstack), 3)
        self.assertEqual(callstack[0].function_name, "halt")
        self.assertEqual(callstack[1].function_name, "ns::foo")
        self.assertEqual(callstack[2].function_name, "main")

    @parameterized.expand([1, 10, 50])
    def test_top_callstack_with_parsing(self, recursion_count: int):
        lib.write_words_to_device(self.core_loc, 0x4000, recursion_count, 0, self.context)
        elf_path = self.get_elf_path("callstack")
        self.loader.run_elf(elf_path)
        with self.risc_debug.ensure_halted():
            pc = self.risc_debug.read_gpr(32)
        parsed_elf = lib.parse_elf(elf_path, self.context)
        callstack: list[CallstackEntry] = lib.top_callstack(pc, parsed_elf, None, self.context)
        self.assertEqual(len(callstack), 1)
        self.assertEqual(callstack[0].function_name, "halt")

    @parameterized.expand([1, 10, 50])
    def test_top_callstack(self, recursion_count):
        lib.write_words_to_device(self.core_loc, 0x4000, recursion_count, 0, self.context)
        elf_path = self.get_elf_path("callstack")
        self.loader.run_elf(elf_path)
        with self.risc_debug.ensure_halted():
            pc = self.risc_debug.read_gpr(32)
        callstack: list[CallstackEntry] = lib.top_callstack(pc, elf_path, None, self.context)
        self.assertEqual(len(callstack), 1)
        self.assertEqual(callstack[0].function_name, "halt")

    @parameterized.expand([(1, 1), (10, 9), (50, 49)])
    def test_callstack_optimized(self, recursion_count, expected_f1_on_callstack_count):

        if self.is_wormhole() and self.is_eth_block():
            self.skipTest("Callstack optimized tests break on ETH blocks")

        lib.write_words_to_device(self.core_loc, 0x4000, recursion_count, 0, self.context)
        elf_path = self.get_elf_path("callstack.optimized")
        self.loader.run_elf(elf_path)
        callstack: list[CallstackEntry] = lib.callstack(
            self.core_loc, elf_path, None, self.risc_name, None, 100, True, False, 0, self.context
        )

        self.assertEqual(len(callstack), expected_f1_on_callstack_count + 2)
        for i in range(0, expected_f1_on_callstack_count):
            self.assertEqual(callstack[i].function_name, "f1")
        self.assertEqual(callstack[expected_f1_on_callstack_count + 0].function_name, "recurse")
        self.assertEqual(callstack[expected_f1_on_callstack_count + 1].function_name, "main")

    @parameterized.expand([(1, 1)])
    def test_top_callstack_optimized(self, recursion_count: int, expected_f1_on_callstack_count: int):

        if self.is_wormhole() and self.is_eth_block():
            self.skipTest("Callstack optimized tests break on ETH blocks")

        lib.write_words_to_device(self.core_loc, 0x4000, recursion_count, 0, self.context)
        elf_path = self.get_elf_path("callstack.optimized")
        self.loader.run_elf(elf_path)
        with self.risc_debug.ensure_halted():
            pc = self.risc_debug.read_gpr(32)
        callstack: list[CallstackEntry] = lib.top_callstack(pc, elf_path, None, self.context)

        self.assertEqual(len(callstack), expected_f1_on_callstack_count + 2)
        for i in range(0, expected_f1_on_callstack_count):
            self.assertEqual(callstack[i].function_name, "f1")
        self.assertEqual(callstack[expected_f1_on_callstack_count + 0].function_name, "recurse")
        self.assertEqual(callstack[expected_f1_on_callstack_count + 1].function_name, "main")

    @parameterized.expand(
        [
            ("abcd", "build/riscv-src/blackhole/callstack.brisc.elf"),  # Invalid core_loc string
            ("0,0", "invalid_elf_path"),  # Invalid elf path
            (
                "0,0",
                ["build/riscv-src/blackhole/callstack.brisc.elf", "invalid_elf_path"],
            ),  # One of elf paths is invalid
            (
                "0,0",
                ["build/riscv-src/blackhole/callstack.brisc.elf"],
                [0, 1],
            ),  # Length of elf_paths and offsets is different
            ("0,0", "build/riscv-src/blackhole/callstack.brisc.elf", 0, "invalid"),  # Invalid risc_name
            ("0,0", "build/riscv-src/blackhole/callstack.brisc.elf", 0, "brisc", -1),  # Invalid max_depth (too low)
            ("0,0", "build/riscv-src/blackhole/callstack.brisc.elf", 0, "brisc", 1, -1),  # Invalid device_id
        ]
    )
    def test_callstack_invalid(self, core_loc, elf_paths, offsets=None, risc_name="brisc", max_depth=100, device_id=0):
        """Test invalid inputs for callstack function."""

        # Check for invalid core_loc
        with self.assertRaises((util.TTException, ValueError, FileNotFoundError)):
            lib.callstack(
                core_loc, elf_paths, offsets, risc_name, None, max_depth, True, False, device_id, self.context
            )
