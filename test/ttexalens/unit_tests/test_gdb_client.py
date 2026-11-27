# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest

from parameterized import parameterized

from ttexalens.gdb.gdb_client import get_callstack_entry


class TestGetCallstackEntry(unittest.TestCase):
    @parameterized.expand(
        [
            ("template", "#0  0x00001234 in ckernel::foo<1u> (a=1) at k.cpp:5", 0x1234, "ckernel::foo<1u>", "k.cpp", 5),
            (
                "call_operator",
                "#1  0x00002345 in ckernel::Op::operator() (this=0x0) at k.cpp:10",
                0x2345,
                "ckernel::Op::operator()",
                "k.cpp",
                10,
            ),
        ]
    )
    def test_frame_line(self, _name: str, line: str, pc: int, function_name: str, file: str, line_number: int):
        entry = get_callstack_entry(line)
        self.assertEqual(entry.pc, pc)
        self.assertEqual(entry.function_name, function_name)
        file_info = (entry.file_info.file, entry.file_info.line) if entry.file_info is not None else None
        self.assertEqual(file_info, (file, line_number))


if __name__ == "__main__":
    unittest.main()
