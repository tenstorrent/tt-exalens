# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

# Host-only tests for the GDB client helpers: parsing backtrace lines and looking up the core to debug.
# No device is needed.

import unittest
from unittest.mock import MagicMock, patch

from parameterized import parameterized

from ttexalens.exceptions import TTException
from ttexalens.gdb.gdb_client import get_callstack_entry, get_gdb_callstack


class TestGdbBacktraceParsing(unittest.TestCase):
    @parameterized.expand(
        [
            ("plain", "#0  halt () at /k.cpp:3", None, "halt", "/k.cpp", 3),
            ("pc", "#1  0x00001234 in f1 (a=1) at /k.cpp:37", 0x1234, "f1", "/k.cpp", 37),
            ("namespace", "#1  0x00001234 in ns::foo () at /k.cpp:53", 0x1234, "ns::foo", "/k.cpp", 53),
            (
                "template",
                "#4  0x000019f4 in template_test::TemplateClass<3>::static_method<-1> () at /k.cpp:61",
                0x19F4,
                "template_test::TemplateClass<3>::static_method<-1>",
                "/k.cpp",
                61,
            ),
            (
                "template_args",
                "#0  0x00001234 in ckernel::foo<1u> (a=1) at /k.cpp:5",
                0x1234,
                "ckernel::foo<1u>",
                "/k.cpp",
                5,
            ),
            (
                "operator",
                "#1  ckernel::Op::operator() (this=0x10) at /k.cpp:7",
                None,
                "ckernel::Op::operator()",
                "/k.cpp",
                7,
            ),
            (
                "args_with_parentheses",
                "#2  0x00000020 in run (f=0x30 <g(int)>) at /k.cpp:9",
                0x20,
                "run",
                "/k.cpp",
                9,
            ),
        ]
    )
    def test_frame(self, _name, line, pc, function_name, file_path, line_no):
        entry = get_callstack_entry(line)
        self.assertEqual(entry.pc, pc)
        self.assertEqual(entry.function_name, function_name)
        assert entry.file_info is not None
        self.assertEqual(entry.file_info.file, file_path)
        self.assertEqual(entry.file_info.line, line_no)


class TestGdbCallstackCoreLookup(unittest.TestCase):
    def test_core_not_exposed_by_server_raises_before_starting_gdb(self):
        gdb_server = MagicMock()
        gdb_server.available_processes = {}
        with patch("ttexalens.gdb.gdb_client.subprocess.Popen") as popen:
            with self.assertRaisesRegex(TTException, "does not expose"):
                get_gdb_callstack(MagicMock(), "brisc", None, ["a.elf"], [None], gdb_server)
            popen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
