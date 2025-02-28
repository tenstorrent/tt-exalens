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
