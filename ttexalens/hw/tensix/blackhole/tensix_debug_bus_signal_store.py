# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens.debug_bus_signal_store import DebugBusSignalDescription


debug_bus_signal_map = {
    # For the other signals applying the pc_mask.
    "brisc_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 5 + 1, mask=0x3FFFFFFF),
    "trisc0_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 6 + 1, mask=0x3FFFFFFF),
    "trisc1_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 7 + 1, mask=0x3FFFFFFF),
    "trisc2_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 8 + 1, mask=0x3FFFFFFF),
    "ncrisc_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 12 + 1, mask=0x3FFFFFFF),
}
