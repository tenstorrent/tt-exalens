# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

"""
Device access tracing decorator for auditing tt-triage memory protection coverage.

This module provides a decorator to trace all device register reads and writes,
capturing full stack traces to identify which tt-triage scripts are calling which
operations. This enables verification that all device access is properly protected.

Usage:
    # Enable tracing via environment variables:
    export TTEXALENS_TRACE_DEVICE_ACCESS=1
    export TTEXALENS_TRACE_OUTPUT=/tmp/device_access_trace.jsonl

    # Run your tt-triage script
    python tt-triage/scripts/your_script.py

    # Analyze the trace
    python -m ttexalens.device_access_tracer --analyze /tmp/device_access_trace.jsonl
"""

import json
import os
import threading
import time
import traceback
from functools import wraps
from typing import Any, Callable


class DeviceAccessTracer:
    """Thread-safe tracer for device register access operations."""

    def __init__(self):
        self.enabled = os.environ.get("TTEXALENS_TRACE_DEVICE_ACCESS", "0") == "1"
        self.output_file = os.environ.get("TTEXALENS_TRACE_OUTPUT", "/tmp/device_access_trace.jsonl")
        self.lock = threading.Lock()
        self._file_handle = None

        if self.enabled:
            # Open file in append mode
            self._file_handle = open(self.output_file, "a")

    def __del__(self):
        if self._file_handle:
            self._file_handle.close()

    def trace_access(
        self, operation: str, coord_x: int, coord_y: int, address: int, size_or_data: Any, stack_trace: list
    ):
        """Record a device access operation."""
        if not self.enabled:
            return

        # Determine size
        if operation == "write":
            size = len(size_or_data) if isinstance(size_or_data, bytes) else size_or_data
        else:
            size = size_or_data

        # Build trace record
        record = {
            "timestamp": time.time(),
            "timestamp_str": time.strftime("%Y-%m-%d %H:%M:%S"),
            "operation": operation,
            "coord_x": coord_x,
            "coord_y": coord_y,
            "address": hex(address),
            "size": size,
            "stack_trace": stack_trace,
        }

        # Write atomically
        with self.lock:
            if self._file_handle:
                self._file_handle.write(json.dumps(record) + "\n")
                self._file_handle.flush()


# Global tracer instance
_tracer = DeviceAccessTracer()


def trace_device_access(operation: str):
    """
    Decorator to trace device register access operations.

    Args:
        operation: "read" or "write"

    Returns:
        Decorated function that captures full stack trace for each call
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, coord_x: int, coord_y: int, address: int, size_or_data: Any, *args, **kwargs):
            # Capture full stack trace (excluding this decorator frame)
            stack = traceback.extract_stack()[:-1]  # Exclude decorator frame
            stack_trace = [
                {
                    "file": frame.filename,
                    "line": frame.lineno,
                    "function": frame.name,
                    "code": frame.line if frame.line else "",
                }
                for frame in stack
            ]

            # Record the access
            _tracer.trace_access(operation, coord_x, coord_y, address, size_or_data, stack_trace)

            # Call original function
            return func(self, coord_x, coord_y, address, size_or_data, *args, **kwargs)

        return wrapper

    return decorator


def analyze_trace(trace_file: str):
    """
    Analyze a device access trace file to show which scripts access which addresses.

    Args:
        trace_file: Path to the trace file (JSONL format)
    """
    print(f"Analyzing trace file: {trace_file}\n")

    # Read all records
    records = []
    with open(trace_file, "r") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    print(f"Total operations traced: {len(records)}\n")

    # Group by caller (file, function)
    callers = {}
    for record in records:
        stack = record["stack_trace"]
        if len(stack) >= 2:
            # Get the first frame outside ttexalens (the actual caller)
            caller_frame = None
            for frame in reversed(stack):
                if "ttexalens" not in frame["file"] and "tt-umd" not in frame["file"]:
                    caller_frame = frame
                    break

            if caller_frame:
                key = (caller_frame["file"], caller_frame["function"])
                if key not in callers:
                    callers[key] = {"reads": 0, "writes": 0, "addresses": set()}

                callers[key][f"{record['operation']}s"] += 1
                callers[key]["addresses"].add(record["address"])

    # Print summary
    print("=" * 80)
    print("CALLER SUMMARY")
    print("=" * 80)
    for (file, function), stats in sorted(callers.items()):
        print(f"\nFile: {file}")
        print(f"Function: {function}")
        print(f"  Reads:  {stats['reads']}")
        print(f"  Writes: {stats['writes']}")
        print(f"  Unique addresses accessed: {len(stats['addresses'])}")

    # Show most accessed addresses
    print("\n" + "=" * 80)
    print("MOST ACCESSED ADDRESSES")
    print("=" * 80)
    address_counts = {}
    for record in records:
        addr = record["address"]
        if addr not in address_counts:
            address_counts[addr] = {"reads": 0, "writes": 0}
        address_counts[addr][f"{record['operation']}s"] += 1

    for addr, counts in sorted(address_counts.items(), key=lambda x: x[1]["reads"] + x[1]["writes"], reverse=True)[:20]:
        print(f"{addr}: {counts['reads']} reads, {counts['writes']} writes")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2 and sys.argv[1] == "--analyze":
        analyze_trace(sys.argv[2])
    else:
        print(__doc__)
        print("\nUsage:")
        print("  python -m ttexalens.device_access_tracer --analyze <trace_file>")
