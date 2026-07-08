# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import sys

from abc import abstractmethod
import select
import unittest
import subprocess
import re

from ttexalens import util

# UMD's logger (spdlog) colorizes its output with ANSI escape codes when it believes it is writing to a
# terminal. Depending on the UMD build and environment (notably CI), this can happen even though we read its
# output through a pipe, producing lines like "\x1b[90m<timestamp>\x1b[0m | info | ...". Strip these escapes
# (and any trailing carriage return) as we read, so output matching is not thrown off by invisible bytes.
_ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

_UMD_LOGGER_LEVEL_BY_VERBOSITY = {
    util.Verbosity.NONE: "off",
    util.Verbosity.ERROR: "error",
    util.Verbosity.WARN: "warning",
    util.Verbosity.INFO: "info",
    util.Verbosity.VERBOSE: "info",
    util.Verbosity.DEBUG: "debug",
    util.Verbosity.TRACE: "trace",
}


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
    prompt_regex = r"^(gdb:[^ ]+ )?noc:\d+ device:\d+ loc:\d+-\d+ \(\d+,\d+\) > $"
    umd_log_entry_regex = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+ \| \w+\s*\|\s*\w+ \| .*?\(\w[\w./]*:\d+\)"

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
            r"\(\d+ bytes loaded in [\d.]+s\)",
        ]
        tester.assertGreaterEqual(len(lines), len(test_regex))

        id = 0
        num_test_regex = len(test_regex)

        for line in lines:
            # Strip out any interleaved UMD logger entries, then ignore the line if nothing meaningful remains.
            line = re.sub(self.umd_log_entry_regex, "", line).strip()
            if not line:
                continue

            # Check if the line matches the current test regex
            # Last test regex is a special case, as there may be multiple lines that match it
            # depending on number of devices
            if num_test_regex > 0 and re.search(test_regex[id], line):
                if id < num_test_regex - 1:
                    id += 1
                continue

            # Check if the line matches any of the skip regex patterns
            if any(re.search(regex, line) for regex in skip_regex):
                continue

            # Report an unexpected line
            expected = test_regex[id] if num_test_regex > 0 else "<no expected lines>"
            tester.fail(f"Unexpected line: {line}, expected {expected}")


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
        os.environ["TT_LOGGER_LEVEL"] = _UMD_LOGGER_LEVEL_BY_VERBOSITY[util.Verbosity.get()]
        self.process = subprocess.Popen(
            program_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return self.process

    def start(self, tester: unittest.TestCase, args=None):
        self.invoke(args)
        self.verifier.verify_start(self, tester)

    def readline(self, timeoutSeconds: float = 60):
        assert self.process is not None
        assert self.process.stdout is not None and self.process.stderr is not None
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
        line = rlist[0].readline()
        if line.endswith("\n"):
            line = line[:-1]
        elif not line:
            return None
        # Strip ANSI color escapes (emitted by UMD's logger) and any trailing carriage return so downstream
        # matching (prompt detection, startup verification) operates on clean text.
        line = _ANSI_ESCAPE_RE.sub("", line).rstrip("\r")
        print(line)
        return line

    def writeline(self, line):
        assert self.process is not None and self.process.stdin is not None
        self.process.stdin.write(line)
        self.process.stdin.write("\n")
        self.process.stdin.flush()

    def read_until_prompt(self, readline_timeout: float = 60) -> tuple[list[str], str | None]:
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
        except Exception:
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
        util.Verbosity.set(util.Verbosity.DEBUG)
        runner = TTExaLensTestRunner(UmdTTExaLensOutputVerifier())
        runner.start(self)
        runner.writeline("x")
        runner.wait()
        self.assertEqual(runner.returncode, 0)


if __name__ == "__main__":
    unittest.main()
