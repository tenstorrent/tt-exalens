# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import sys

from abc import abstractmethod
import select
import unittest
import subprocess
import re


class TTExaLensOutputVerifier:
    def __init__(self):
        pass

    def verify_start(self, runner: "TTExaLensTestRunner", tester: unittest.TestCase):
        lines, prompt = runner.read_until_prompt()
        assert prompt is not None
        self.verify_startup(lines, prompt, tester)

    @abstractmethod
    def is_prompt_line(self, line: str) -> bool:
        pass

    @abstractmethod
    def verify_startup(self, lines: list, prompt: str, tester: unittest.TestCase):
        pass


class UmdTTExaLensOutputVerifier(TTExaLensOutputVerifier):
    prompt_regex = r"^(gdb:[^ ]+ )?([[]4B MODE[\]] )?noc:\d+ device:\d+ loc:\d+-\d+ \(\d+,\d+\) > $"

    def __init__(self):
        self.server_temp_path = ""

    def is_prompt_line(self, line: str) -> bool:
        return re.match(self.prompt_regex, line) is not None

    def verify_startup(self, lines: list, prompt: str, tester: unittest.TestCase):
        test_regex: list[str] = []
        skip_regex = [
            r"Verbosity level: \d+",
            r"Output directory \(output_dir\) was not supplied and cannot be determined automatically\. Continuing with limited functionality\.\.\.",
            r"Device opened successfully.",
            r"Opened device: id=\d+, arch=\w+, has_mmio=\w+, harvesting=",
            r".*ttSiliconDevice::init_hugepage:.*",
            r"Loading yaml file: '([^']*\.yaml)'",
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


class TTExaLensTestRunner:
    def __init__(self, verifier: TTExaLensOutputVerifier):
        self.interpreter_path = sys.executable
        self.ttexalens_py_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../..", "tt-exalens.py")
        self.process: subprocess.Popen | None = None
        self.verifier = verifier

    @property
    def is_running(self):
        if self.process is None or not self.process.returncode is None:
            return False
        return self.process.poll() is None

    @property
    def returncode(self):
        assert self.process is not None
        return self.process.returncode

    def invoke(self, args=None):
        program_args = [self.interpreter_path, "-u", self.ttexalens_py_path]
        if not args is None:
            if not type(args) == list:
                args = [args]
        if os.getenv("TTEXALENS_TESTS_USE_NOC1", "0") == "1":
            program_args.append("--use-noc1")
        self.process = subprocess.Popen(
            program_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return self.process

    def start(self, tester: unittest.TestCase, args=None):
        self.invoke(args)
        self.verifier.verify_start(self, tester)

    def readline(self, timeoutSeconds: float = 7):
        assert self.process is not None
        # Fast path for program that ended
        rlist, _, _ = select.select([self.process.stdout, self.process.stderr], [], [], 0)
        if len(rlist) == 0:
            if not self.is_running:
                return None
            rlist, _, _ = select.select([self.process.stdout, self.process.stderr], [], [], timeoutSeconds)
            if len(rlist) == 0:
                if not self.is_running:
                    return None
                raise Exception(f"Hit timeout ({timeoutSeconds}s) while waiting for output from TTExaLens")
        line = rlist[0].readline()  # type: ignore
        if line.endswith("\n"):
            line = line[:-1]
        elif not line:
            return None
        print(line)
        return line

    def writeline(self, line):
        assert self.process is not None and self.process.stdin is not None
        self.process.stdin.write(line)
        self.process.stdin.write("\n")
        self.process.stdin.flush()

    def read_until_prompt(self, readline_timeout: float = 7) -> tuple[list[str], str | None]:
        lines: list[str] = []
        while True:
            line = self.readline(readline_timeout)
            if line is None:
                return (lines, None)
            if self.verifier.is_prompt_line(line):
                return (lines, line)
            lines.append(line)

    def wait(self, timeoutSeconds: float | None = None):
        assert self.process is not None
        self.process.wait(timeoutSeconds)

    def kill(self):
        try:
            assert self.process is not None
            self.process.kill()
            self.process.wait()
        except:
            pass

    def execute(self, args=None, input=None, timeout=None):
        try:
            self.invoke(args)
            assert self.process is not None
            stdout, stderr = self.process.communicate(input, timeout)
            return stdout.splitlines(), stderr.splitlines()
        except Exception as e:
            self.kill()
            raise e


class TestUmdTTExaLens(unittest.TestCase):
    def test_startup_and_exit_just_return_code(self):
        runner = TTExaLensTestRunner(UmdTTExaLensOutputVerifier())
        runner.start(self)
        runner.writeline("x")
        runner.wait()
        self.assertEqual(runner.returncode, 0)


if __name__ == "__main__":
    unittest.main()
