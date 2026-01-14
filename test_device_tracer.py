#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

"""
Simple test script to verify device access tracing works.

Usage:
    export TTEXALENS_TRACE_DEVICE_ACCESS=1
    export TTEXALENS_TRACE_OUTPUT=/tmp/test_trace.jsonl
    python test_device_tracer.py

Then analyze:
    python -m ttexalens.device_access_tracer --analyze /tmp/test_trace.jsonl
"""

import os

# Enable tracing before importing ttexalens
os.environ["TTEXALENS_TRACE_DEVICE_ACCESS"] = "1"
os.environ["TTEXALENS_TRACE_OUTPUT"] = "/tmp/test_trace.jsonl"

from ttexalens.device_access_tracer import trace_device_access


# Simulate a method similar to __read_from_device_reg
class MockDevice:
    @trace_device_access("read")
    def read_register(self, coord_x: int, coord_y: int, address: int, size: int) -> bytes:
        """Simulate a device register read."""
        print(f"[MockDevice] Reading from ({coord_x}, {coord_y}) @ {hex(address)}, size={size}")
        return b"\x00" * size

    @trace_device_access("write")
    def write_register(self, coord_x: int, coord_y: int, address: int, data: bytes):
        """Simulate a device register write."""
        print(f"[MockDevice] Writing to ({coord_x}, {coord_y}) @ {hex(address)}, size={len(data)}")


def helper_function():
    """A helper that calls device operations."""
    device = MockDevice()
    device.read_register(0, 0, 0x1000, 4)
    device.write_register(0, 0, 0x2000, b"\xAA\xBB\xCC\xDD")


def main():
    """Main function simulating a tt-triage script."""
    print("Testing device access tracing...")
    print(f"Trace output will be written to: {os.environ.get('TTEXALENS_TRACE_OUTPUT')}")
    print()

    # Call some operations
    device = MockDevice()

    # Direct calls
    device.read_register(0, 0, 0x1000, 4)
    device.write_register(1, 2, 0x2000, b"\xDE\xAD\xBE\xEF")

    # Call through helper
    helper_function()

    print()
    print("Done! Check the trace file:")
    print(f"  cat {os.environ.get('TTEXALENS_TRACE_OUTPUT')}")
    print()
    print("Analyze with:")
    print(f"  python -m ttexalens.device_access_tracer --analyze {os.environ.get('TTEXALENS_TRACE_OUTPUT')}")


if __name__ == "__main__":
    main()
