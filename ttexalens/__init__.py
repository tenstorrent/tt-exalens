# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from .tt_exalens_init import init_ttexalens, init_ttexalens_remote, set_active_context
from .tt_exalens_lib import (
    arc_msg,
    callstack,
    check_context,
    convert_coordinate,
    coverage,
    init_perf_counters,
    list_perf_counters,
    load_elf,
    parse_elf,
    read_arc_telemetry_entry,
    read_from_device,
    read_perf_counters,
    read_register,
    read_riscv_memory,
    read_word_from_device,
    read_words_from_device,
    run_elf,
    start_perf_counters,
    stop_perf_counters,
    top_callstack,
    write_register,
    write_riscv_memory,
    write_to_device,
    write_words_to_device,
    TensixState,
)
from .hardware.perf_counters import PerfCounterBlockDescription, TensixPerfCounters
from .coordinate import OnChipCoordinate
from .context import Context
from .device import Device
from .util import TTException, TTFatalException, Verbosity
from .exceptions import (
    CoordinateTranslationError,
    RestrictedMemoryAccessError,
    UnsafeAccessException,
    TimeoutDeviceRegisterError,
)


__all__ = [
    # context.py
    "Context",
    # coordinate.py
    "CoordinateTranslationError",
    "OnChipCoordinate",
    # device.py
    "Device",
    # tt_exalens_init.py
    "init_ttexalens",
    "init_ttexalens_remote",
    "set_active_context",
    # tt_exalens_lib.py
    "arc_msg",
    "callstack",
    "check_context",
    "convert_coordinate",
    "coverage",
    "init_perf_counters",
    "list_perf_counters",
    "load_elf",
    "parse_elf",
    "read_arc_telemetry_entry",
    "read_from_device",
    "read_perf_counters",
    "read_word_from_device",
    "read_words_from_device",
    "read_register",
    "read_riscv_memory",
    "run_elf",
    "start_perf_counters",
    "stop_perf_counters",
    "TensixState",
    "top_callstack",
    "write_register",
    "write_riscv_memory",
    "write_to_device",
    "write_words_to_device",
    # hardware/perf_counters.py
    "PerfCounterBlockDescription",
    "TensixPerfCounters",
    # util.py
    "TTException",
    "TTFatalException",
    "Verbosity",
    "RestrictedMemoryAccessError",
    "UnsafeAccessException",
    "TimeoutDeviceRegisterError",
]
