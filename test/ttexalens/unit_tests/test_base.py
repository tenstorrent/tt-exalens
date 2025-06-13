# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttexalens import tt_exalens_init
import os


def init_default_test_context():
    if os.getenv("TTEXALENS_TESTS_REMOTE"):
        ip_address = os.getenv("TTEXALENS_TESTS_REMOTE_ADDRESS", "localhost")
        port = int(os.getenv("TTEXALENS_TESTS_REMOTE_PORT", "5555"))
        return tt_exalens_init.init_ttexalens_remote(ip_address, port)
    else:
        return tt_exalens_init.init_ttexalens()


def init_test_context(use_noc1: bool = False):
    if use_noc1:
        assert not os.getenv("TTEXALENS_TESTS_REMOTE"), "Remote testing for NOC1 not supported"
        return tt_exalens_init.init_ttexalens(use_noc1=True)
    else:
        return init_default_test_context()
