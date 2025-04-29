# SPDX-FileCopyrightText: (c) 2025 Tenstorrent AI ULC
#
# SPDX-License-Identifier: Apache-2.0
from ttexalens import tt_exalens_init
from ttexalens.tt_exalens_lib import read_tensix_register, write_tensix_register, read_riscv_memory

regs = [
    "NIU_MST_ATOMIC_RESP_RECEIVED",
    "NIU_MST_WR_ACK_RECEIVED",
    "NIU_MST_RD_RESP_RECEIVED",
    "NIU_MST_RD_DATA_WORD_RECEIVED",
    "NIU_MST_CMD_ACCEPTED",
    "NIU_MST_RD_REQ_SENT",
    "NIU_MST_NONPOSTED_ATOMIC_SENT",
    "NIU_MST_POSTED_ATOMIC_SENT",
    "NIU_MST_NONPOSTED_WR_DATA_WORD_SENT",
    "NIU_MST_POSTED_WR_DATA_WORD_SENT",
    "NIU_MST_NONPOSTED_WR_REQ_SENT",
    "NIU_MST_POSTED_WR_REQ_SENT",
    "NIU_MST_NONPOSTED_WR_REQ_STARTED",
    "NIU_MST_POSTED_WR_REQ_STARTED",
    "NIU_MST_RD_REQ_STARTED",
    "NIU_MST_NONPOSTED_ATOMIC_STARTED",
    "NIU_MST_REQS_OUTSTANDING_ID",
    "NIU_MST_WRITE_REQS_OUTGOING_ID",
    "NIU_SLV_ATOMIC_RESP_SENT",
    "NIU_SLV_WR_ACK_SENT",
    "NIU_SLV_RD_RESP_SENT",
    "NIU_SLV_RD_DATA_WORD_SENT",
    "NIU_SLV_REQ_ACCEPTED",
    "NIU_SLV_RD_REQ_RECEIVED",
    "NIU_SLV_NONPOSTED_ATOMIC_RECEIVED",
    "NIU_SLV_POSTED_ATOMIC_RECEIVED",
    "NIU_SLV_NONPOSTED_WR_DATA_WORD_RECEIVED",
    "NIU_SLV_POSTED_WR_DATA_WORD_RECEIVED",
    "NIU_SLV_NONPOSTED_WR_REQ_RECEIVED",
    "NIU_SLV_POSTED_WR_REQ_RECEIVED",
    "NIU_SLV_NONPOSTED_WR_REQ_STARTED",
    "NIU_SLV_POSTED_WR_REQ_STARTED",
]

vars = {
    "noc_reads_num_issued": (0xFFB00038, "NIU_MST_RD_RESP_RECEIVED"),
    "noc_nonposted_writes_num_issued": (0xFFB00030, "NIU_MST_NONPOSTED_WR_REQ_SENT"),
    "noc_nonposted_writes_acked": (0xFFB00028, "NIU_MST_WR_ACK_RECEIVED"),
    "noc_nonposted_atomics_acked": (0xFFB00020, "NIU_MST_ATOMIC_RESP_RECEIVED"),
    "noc_posted_writes_num_issued": (0xFFB00018, "NIU_MST_POSTED_WR_REQ_SENT"),
}

for var in vars:
    core_loc = "0,0"
    #    write_tensix_register(core_loc, reg, 1)
    addr, reg = vars[var]
    print(f"{var}: {read_riscv_memory(core_loc, addr)} --> {read_tensix_register(core_loc, reg)}")
