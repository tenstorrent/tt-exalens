# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens.tt_exalens_init import init_ttexalens
from ttexalens.tt_exalens_lib import read_word_from_device

context = init_ttexalens(safe_mode=False, use_noc1=True)
device = context.devices[0]
location = device.arc_block.location

for i in range(5):
    print(f"{i}: {hex(read_word_from_device(location, 0, context=context, noc_id=0))}")
