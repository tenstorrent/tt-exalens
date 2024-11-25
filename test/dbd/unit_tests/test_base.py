# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from dbd import tt_debuda_init
import os

def init_default_test_context():
    if os.getenv('TTLENS_TESTS_REMOTE'):
        ip_address = os.getenv('TTLENS_TESTS_REMOTE_ADDRESS', 'localhost')
        port = int(os.getenv('TTLENS_TESTS_REMOTE_PORT', '5555'))
        return tt_debuda_init.init_debuda_remote(ip_address, port)
    else:
        return tt_debuda_init.init_debuda()
