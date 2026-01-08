# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttexalens import init_ttexalens_remote, init_ttexalens, OnChipCoordinate, Device
import os

# Global cache for simulator context to ensure only one simulator process
# is created when TTEXALENS_SIMULATOR is set, preventing conflicts between
# parameterized test classes
_cached_simulator_context = None

# Speeding up tests by not executing UMD initialization every time
# We are using class parameterized tests which cause multiple
# initializations of the test context
_cached_test_context = None


def init_default_test_context():
    global _cached_simulator_context
    global _cached_test_context

    if os.getenv("TTEXALENS_TESTS_REMOTE"):
        ip_address = os.getenv("TTEXALENS_TESTS_REMOTE_ADDRESS", "localhost")
        port = int(os.getenv("TTEXALENS_TESTS_REMOTE_PORT", "5555"))
        _cached_test_context = init_ttexalens_remote(ip_address, port, use_4B_mode=False)
    elif os.getenv("TTEXALENS_SIMULATOR"):
        # Reuse cached simulator context to prevent multiple simulator processes
        if _cached_simulator_context is None:
            simulation_directory = os.getenv("TTEXALENS_SIMULATOR")
            _cached_simulator_context = init_ttexalens(simulation_directory=simulation_directory, use_4B_mode=False)
        return _cached_simulator_context
    else:
        _cached_test_context = init_ttexalens(use_4B_mode=False)
    return _cached_test_context


def init_cached_test_context():
    global _cached_test_context
    if _cached_test_context is None:
        _cached_test_context = init_default_test_context()
    return _cached_test_context


def init_test_context(use_noc1: bool = False):
    if use_noc1:
        assert not os.getenv("TTEXALENS_TESTS_REMOTE"), "Remote testing for NOC1 not supported"
        return init_ttexalens(use_noc1=True, use_4B_mode=False)
    else:
        return init_default_test_context()


def get_core_location(core_desc: str, device: Device) -> OnChipCoordinate:
    """Convert core_desc to core location string."""
    if core_desc.startswith("ETH"):
        eth_blocks = device.idle_eth_blocks
        core_index = int(core_desc[3:])
        if len(eth_blocks) > core_index:
            return eth_blocks[core_index].location
        raise ValueError(f"ETH core {core_index} not available on this platform")

    elif core_desc.startswith("FW"):
        fw_cores = device.get_block_locations(block_type="functional_workers")
        core_index = int(core_desc[2:])
        if len(fw_cores) > core_index:
            return fw_cores[core_index]
        raise ValueError(f"FW core {core_index} not available on this platform")
    elif core_desc.startswith("DRAM"):
        dram_cores = device.get_block_locations(block_type="dram")
        core_index = int(core_desc[4:])
        if len(dram_cores) > core_index:
            return dram_cores[core_index]
        raise ValueError(f"DRAM core {core_index} not available on this platform")

    try:
        return OnChipCoordinate.create(core_desc, device=device)
    except:
        raise ValueError(f"Unknown core description {core_desc}")
