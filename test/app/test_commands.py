# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import sys

from abc import abstractmethod
import select
import unittest
import subprocess
import re

from test.app.test_umd_debuda import DbdTestRunner,UmdDbdOutputVerifier

class CommandTests(unittest.TestCase):
    def check_written_lines(self,lines, match_hex):
        # Removing first and last lines since they do not values that we are interested in
        lines = lines[1:-1]

        pattern = r"0x[0-9a-fA-F]+:\s+([0-9a-fA-F\s]+)"
        
        for line in lines:
            matches = re.findall(pattern, line)
            
            for match in matches:
                values = match.split()
                for value in values:
                    if value.lower() != match_hex.lower():
                        return False 
                            
            return True  

    def test_bwxy_command(self):
        runner = DbdTestRunner(UmdDbdOutputVerifier())
        runner.start(self)

        test_hex = "a5a5a5a5"

        # Reseting memory
        runner.writeline("bwxy 18-18 0x0 16 --fill 0")
        runner.read_all_non_blocking()
        runner.writeline(f"bwxy 18-18 0x0 16 --fill 0x{test_hex}")
        runner.read_all_non_blocking()
        
        runner.writeline("brxy 18-18 0x0 16")
        read_lines = runner.read_all_non_blocking()

        runner.writeline("x")
        runner.wait()

        self.assertEqual(self.check_written_lines(read_lines, test_hex),True)
        self.assertEqual(runner.returncode, 0)