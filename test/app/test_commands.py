# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import sys

from abc import abstractmethod
import select
import unittest
import subprocess
import re
import time

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
        print("BWXY")
        runner = DbdTestRunner(UmdDbdOutputVerifier())
        runner.start(self)

        address = "0-0"
        test_hex = "a5a5a5a5"
        print("CI CHECK: test0")
        # Reseting memory
        runner.writeline(f"bwxy {address} 0x0 16 --fill 0")
        print("CI CHECK: test1")

        time.sleep(1)
        runner.read_all_non_blocking()
        print("CI CHECK: test2")
        runner.writeline(f"bwxy {address} 0x0 16 --fill 0x{test_hex}")
        print("CI CHECK: test3")
        time.sleep(1)
        runner.read_all_non_blocking()             
        
        runner.writeline(f"brxy {address} 0x0 16")
        time.sleep(1)
        read_lines = runner.read_all_non_blocking()

        runner.writeline("x")
        runner.wait()

        self.assertEqual(self.check_written_lines(read_lines, test_hex),True)
        self.assertEqual(runner.returncode, 0)