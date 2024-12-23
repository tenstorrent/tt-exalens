# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_lens_init
import os


def init_default_test_context():
    if os.getenv("TTLENS_TESTS_REMOTE"):
        ip_address = os.getenv("TTLENS_TESTS_REMOTE_ADDRESS", "localhost")
        port = int(os.getenv("TTLENS_TESTS_REMOTE_PORT", "5555"))
        return tt_lens_init.init_ttlens_remote(ip_address, port)
    else:
        return tt_lens_init.init_ttlens()
