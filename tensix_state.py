# SPDX-FileCopyrightText: (c) 2026 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens import OnChipCoordinate
from ttexalens.tt_exalens_lib import get_tensix_state
from ttexalens.tt_exalens_init import init_ttexalens

context = init_ttexalens()
device = context.devices[0]
location = OnChipCoordinate.create("0,0", device)
tensix_state = get_tensix_state("0,0")
tensix_state2 = get_tensix_state(location)

print(tensix_state == tensix_state2)
