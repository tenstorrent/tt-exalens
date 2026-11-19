# SPDX-FileCopyrightText: © 2026 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.debug_tensix import TensixDebug


class BlackholeTensixDebug(TensixDebug):
    dest_risc_name = "trisc0"
