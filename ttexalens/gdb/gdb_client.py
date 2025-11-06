# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import os
import re
import subprocess
from ttexalens import util as util
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.gdb.gdb_communication import ServerSocket
from ttexalens.gdb.gdb_server import GdbServer
from ttexalens.hardware.risc_debug import CallstackEntry
from ttexalens.tt_exalens_lib import check_context


def get_gdb_client_path():
    sfpi_path = "sfpi/compiler/bin/riscv-tt-elf-gdb"
    gdb_client_path = os.path.abspath(os.path.join(util.application_path(), sfpi_path))
    if not os.path.isfile(gdb_client_path):
        gdb_client_path = os.path.abspath(os.path.join(util.application_path(), "../build_riscv", sfpi_path))
    return gdb_client_path


def make_add_symbol_file_command(paths: list[str], offsets: list[int | None]) -> str:
    add_symbol_file_cmd = ""
    for path, offset in zip(paths, offsets):
        add_symbol_file_cmd += (
            f"\tadd-symbol-file {path} {offset}\n" if offset is not None else f"\tadd-symbol-file {path}\n"
        )

    # Removing first tab symbol and last new line symbol for prettier look of gdb script
    return add_symbol_file_cmd[1:-1]


def make_gdb_script_for_callstack(
    pid: int,
    elf_paths: list[str],
    offsets: list[int | None],
    port: int,
    start_callstack_label: str,
    end_callstack_label: str,
) -> str:
    return f"""\
        target extended-remote localhost:{port}
        set prompt
        attach {pid}
        {make_add_symbol_file_command(elf_paths, offsets)}
        printf "{start_callstack_label}\\n"
        backtrace
        printf "{end_callstack_label}\\n"
        detach
        quit
    """


def get_process_ids(gdb_server: GdbServer):
    process_ids: dict[OnChipCoordinate, dict[str, int]] = {}
    for pid, process in gdb_server.available_processes.items():
        location = process.risc_debug.risc_location.location
        risc_name = process.risc_debug.risc_location.risc_name

        if location in process_ids:
            process_ids[location][risc_name] = pid
        else:
            process_ids[location] = {risc_name: pid}

    return process_ids


def get_callstack_entry(line: str) -> CallstackEntry:
    pattern = re.compile(
        r"#\d+\s+"  # Skip the frame number
        r"(?:(?P<pc>0x[0-9a-fA-F]+)\s+in\s+)?"  # Capture pc if available
        r"(?P<function_name>\w+(::\w+)*)"  # Capture function name
        r"(?:\s*\(.*?\))?"  # Ignore parentheses
        r"\s+at\s+"  # Skip at
        r"(?P<file_path>.*?):(?P<line>\d+)"  # Capture file path and line
    )

    entry = CallstackEntry()
    match = pattern.match(line)
    if match:
        entry.pc = int(match.groupdict()["pc"], 16) if match.groupdict()["pc"] is not None else None
        entry.function_name = match.groupdict()["function_name"]
        entry.file = match.groupdict()["file_path"]
        entry.line = int(match.groupdict()["line"]) if match.groupdict()["line"] is not None else None

    return entry


def extract_callstack_from_gdb_output(
    gdb_output: str, start_callstack_label: str, end_callstack_label: str
) -> list[CallstackEntry]:
    cs: list[CallstackEntry] = []
    is_cs = False

    current_line = ""
    for line in gdb_output.splitlines():
        if start_callstack_label in line:
            is_cs = True
        elif end_callstack_label in line:
            is_cs = False
        else:
            if is_cs:
                if "#" in line:
                    if current_line != "":
                        cs.append(get_callstack_entry(current_line))
                        current_line = ""

                    current_line += line.strip()
                # Ensure every callstack entry is in one line
                else:
                    current_line += " "
                    current_line += line.strip()

    if current_line != "":
        cs.append(get_callstack_entry(current_line))
        current_line = ""

    # We implicitly skip last line since it is message not callstack entry
    return cs


def get_gdb_callstack(
    location: OnChipCoordinate,
    risc_name: str,
    elf_paths: list[str],
    offsets: list[int | None],
    gdb_server: GdbServer | None = None,
    context: Context | None = None,
) -> list[CallstackEntry]:
    gdb_server_created = False
    if gdb_server is None:
        server = ServerSocket()
        server.start()
        context = check_context(context)
        gdb_server = GdbServer(context, server)
        gdb_server.start()
        gdb_server_created = True
    process_ids = get_process_ids(gdb_server)

    try:
        # Start GDB client
        gdb_client = subprocess.Popen(
            [get_gdb_client_path()],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Labels for determining where backtrace output is
        start_callstack_label = "START CALLSTACK"
        end_callstack_label = "END CALLSTACK"

        assert gdb_server.server.port is not None
        gdb_script = make_gdb_script_for_callstack(
            process_ids[location][risc_name],
            elf_paths,
            offsets,
            gdb_server.server.port,
            start_callstack_label,
            end_callstack_label,
        )

        # Run gdb script
        if gdb_client.stdin is not None:
            gdb_client.stdin.write(gdb_script)
            gdb_client.stdin.flush()

        callstack = extract_callstack_from_gdb_output(
            gdb_client.communicate()[0], start_callstack_label, end_callstack_label
        )
        return callstack
    finally:
        if gdb_server_created:
            gdb_server.stop()
