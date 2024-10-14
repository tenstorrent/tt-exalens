# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import sys

from abc import abstractmethod
import select
import unittest
import subprocess
import re

import os
import fcntl
import select


class DbdOutputVerifier:
    def __init__(self):
        pass

    def verify_start(self, runner: "DbdTestRunner", tester: unittest.TestCase):
        lines, prompt = runner.read_until_prompt()
        self.verify_startup(lines, prompt, tester)
        pass

    @abstractmethod
    def is_prompt_line(self, line: str) -> str:
        pass

    @abstractmethod
    def verify_startup(self, lines: list, prompt: str, tester: unittest.TestCase):
        pass

class UmdDbdOutputVerifier(DbdOutputVerifier):
    prompt_regex = r"^gdb:[^ ]+ device:\d+ loc:\d+-\d+ \(\d+, \d+\) > $"

    def __init__(self):
        self.server_temp_path = ""

    def is_prompt_line(self, line: str) -> str:
        return re.match(self.prompt_regex, line)

    def verify_startup(self, lines: list, prompt: str, tester: unittest.TestCase):
        test_regex = []
        skip_regex = [r"Verbosity level: \d+",
                      r"Output directory \(output_dir\) was not supplied and cannot be determined automatically\. Continuing with limited functionality\.\.\.",
                      r"Device opened successfully.",
                      r"Opened device: id=\d+, arch=\w+, has_mmio=\w+, harvesting=",
                      r".*ttSiliconDevice::init_hugepage:.*",
                      r"Loading yaml file: '([^']*\.yaml)'"
        ]
        tester.assertGreaterEqual(len(lines), len(test_regex))

        id = 0
        num_test_regex = len(test_regex)

        for line in lines:
            # Check if the line matches the current test regex
            # Last test regex is a special case, as there may be multiple lines that match it
            # depending on number of devices
            if re.search(test_regex[id], line):
                if id < num_test_regex - 1:
                    id += 1
                continue
            
            # Check if the line matches any of the skip regex patterns
            if any(re.search(regex, line) for regex in skip_regex):
                continue
            
            # Report an unexpected line
            tester.fail(f"Unexpected line: {line}, expected {test_regex[id]}")
        
        return True

class DbdTestRunner:
    def __init__(self, verifier: DbdOutputVerifier):
        self.interpreter_path = sys.executable
        self.debuda_py_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..", "debuda.py")
        self.process: subprocess.Popen = None
        self.verifier = verifier

    @property
    def is_running(self):
        if self.process is None or not self.process.returncode is None:
            return False
        return self.process.poll() is None
    
    @property
    def returncode(self):
        return self.process.returncode

    def invoke(self, args = None):
        program_args = [self.interpreter_path, '-u', self.debuda_py_path]
        if not args is None:
            if not type(args) == list:
                args = [args]
        self.process = subprocess.Popen(program_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return self.process

    def start(self, tester: unittest.TestCase, args = None):
        self.invoke(args)
        self.verifier.verify_start(self, tester)

    def readline(self, timeoutSeconds:float = 1):
        print("CI CHECK 1---------------------------------------------------")
        if self.process.poll() is None:
            print("Process is running")
        else:
            print("Process has terminated with exit code:", self.process.poll())
        
        # Fast path for program that ended
        rlist, _, _ = select.select([self.process.stdout, self.process.stderr], [], [], 0)
        if len(rlist) == 0:
            if not self.is_running:
                return None
            rlist, _, _ = select.select([self.process.stdout, self.process.stderr], [], [], timeoutSeconds)
            if len(rlist) == 0:
                if not self.is_running:
                    return None
                raise Exception(f"Hit timeout ({timeoutSeconds}s) while waiting for output from Debuda")
        line = rlist[0].readline()
        if line.endswith('\n'):
            line = line[:-1]
        elif not line:
            return None
        print(line)
        return line

    def set_nonblocking(self,fd):
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def read_all_non_blocking(self, timeoutSeconds: float = 1):
        # Fast path for program that ended
        rlist, _, _ = select.select([self.process.stdout, self.process.stderr], [], [], timeoutSeconds)
        
        if len(rlist) == 0:
            if not self.is_running:
                return None
            return []

        original_stdout_flags = fcntl.fcntl(self.process.stdout.fileno(), fcntl.F_GETFL)
        original_stderr_flags = fcntl.fcntl(self.process.stderr.fileno(), fcntl.F_GETFL)

        self.set_nonblocking(self.process.stdout.fileno())
        self.set_nonblocking(self.process.stderr.fileno())

        output_lines = []
        
        for stream in rlist:
            try:
                while True:
                    output = os.read(stream.fileno(), 4096).decode('utf-8')
                    if not output:
                        break
                    
                    lines = output.splitlines()
                    output_lines.extend(lines)
                    for line in lines:
                        print(line)  
            # Passing if os.read gets blocked
            except BlockingIOError:
                pass
        
        fcntl.fcntl(self.process.stdout.fileno(), fcntl.F_SETFL, original_stdout_flags)
        fcntl.fcntl(self.process.stderr.fileno(), fcntl.F_SETFL, original_stderr_flags)

        return output_lines if output_lines else None

    def writeline(self, line):
        self.process.stdin.write(line)
        self.process.stdin.write('\n')
        self.process.stdin.flush()

    def read_until_prompt(self, readline_timeout: float = 1):
        lines = []
        while True:
            line = self.readline(readline_timeout)
            if line is None:
                return (lines, None)
            if self.verifier.is_prompt_line(line):
                return (lines, line)
            lines.append(line)

    def wait(self, timeoutSeconds:float = None):
        self.process.wait(timeoutSeconds)

    def kill(self):
        try:
            self.process.kill()
            self.process.wait()
        except:
            pass

    def execute(self, args = None, input = None, timeout = None):
        try:
            self.invoke(args)
            stdout, stderr = self.process.communicate(input, timeout)
            return stdout.splitlines(), stderr.splitlines()
        except Exception as e:
            self.kill()
            raise e

class TestUmdDebuda(unittest.TestCase):
    @unittest.skip("Disabling this test for the moment. Something not working in CI, investigation needed.")
    def test_startup_and_exit_just_return_code(self):
        runner = DbdTestRunner(UmdDbdOutputVerifier())
        runner.start(self)
        runner.writeline("x")
        runner.wait()
        self.assertEqual(runner.returncode, 0)

if __name__ == "__main__":
    unittest.main()
