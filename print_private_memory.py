# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens import tt_exalens_init
from ttexalens.tt_exalens_lib import read_riscv_memory, read_tensix_register

reg_val = read_tensix_register("0,0", "NIU_MST_WR_ACK_RECEIVED")
print(reg_val)
for i in range(1024):
    val = read_riscv_memory("0,0", 0xFFB00000 + 4 * i)
    print(f"{hex(0xFFB00000 + 4*i)} --> {val}")
