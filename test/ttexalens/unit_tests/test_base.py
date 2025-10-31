# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttexalens import tt_exalens_init
import os

# Global cache for simulator context to ensure only one simulator process
# is created when TTEXALENS_SIMULATOR is set, preventing conflicts between
# parameterized test classes
_cached_simulator_context = None


def init_default_test_context():
    global _cached_simulator_context

    if os.getenv("TTEXALENS_TESTS_REMOTE"):
        ip_address = os.getenv("TTEXALENS_TESTS_REMOTE_ADDRESS", "localhost")
        port = int(os.getenv("TTEXALENS_TESTS_REMOTE_PORT", "5555"))
        return tt_exalens_init.init_ttexalens_remote(ip_address, port)
    elif os.getenv("TTEXALENS_SIMULATOR"):
        # Reuse cached simulator context to prevent multiple simulator processes
        if _cached_simulator_context is None:
            simulation_directory = os.getenv("TTEXALENS_SIMULATOR")
            _cached_simulator_context = tt_exalens_init.init_ttexalens(simulation_directory=simulation_directory)
        return _cached_simulator_context
    else:
        return tt_exalens_init.init_ttexalens()


def init_test_context(use_noc1: bool = False):
    if use_noc1:
        assert not os.getenv("TTEXALENS_TESTS_REMOTE"), "Remote testing for NOC1 not supported"
        return tt_exalens_init.init_ttexalens(use_noc1=True)
    else:
        return init_default_test_context()
