# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens.tt_exalens_init import init_ttexalens
from ttexalens.tt_exalens_lib import read_word_from_device

context = init_ttexalens()
device = context.devices[0]
eth_blocks = device.get_blocks(block_type="idle_eth")
for eth_block in eth_blocks:
    print(eth_block.location)
