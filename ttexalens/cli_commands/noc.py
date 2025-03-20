# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

"""
Usage:
    noc status [-d <device>] [-noc <noc-id>] [-l <loc>] [-s]
    noc dump [-d <device>] [-l <loc>] [-s]

Arguments:
    device-id         ID of the device [default: current active]
    noc-id            Identifier for the NOC (e.g. 0, 1) [default: both noc0 and noc1]
    loc               Location identifier (e.g. 0-0) [default: current active]

Options:
    -s, --simple     Print simple output

Description:
    Dumps NOC registers.
        • "noc status" prints status registers.
        • "noc dump" dumps a continuous block of registers.

Examples:
    noc status -d 0 -l 0,0                      # Prints status registers for device 0 on 0,0
    noc dump                                    # Dumps all registers for device 0 on current core
    noc status -s                               # Prints status registers with simple output
"""

command_metadata = {
    "short": "nc",
    "long": "noc",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc"],
}

from docopt import docopt
from ttexalens import command_parser, util as util
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import read_words_from_device
from ttexalens.uistate import UIState
from typing import List

# Import Rich classes for output.
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

# Create a global console instance.
console = Console()

# State maps for stream registers
phase_state_map = {
    0: "PHASE_START",
    1: "PHASE_AUTO_CONFIG",
    2: "PHASE_AUTO_CONFIG_SENT",
    3: "PHASE_ADVANCE_WAIT",
    4: "PHASE_PREV_DATA_FLUSH_WAIT",
    5: "PHASE_FWD_DATA"
}

dest_state_map = {
    0: "DEST_IDLE",
    1: "DEST_REMOTE",
    2: "DEST_LOCAL",
    3: "DEST_ENDPOINT",
    4: "DEST_NO_FWD"
}

dest_ready_state_map = {
    0: "DEST_READY_IDLE",
    1: "DEST_READY_SEND_FIRST",
    2: "DEST_READY_WAIT_DATA",
    3: "DEST_READY_SEND_SECOND",
    4: "DEST_READY_FWD_DATA"
}

src_ready_state_map = {
    0: "SRC_READY_IDLE",
    1: "SRC_READY_WAIT_CFG",
    2: "SRC_READY_DEST_READY_TABLE_RD",
    3: "SRC_READY_SEND_UPDATE",
    4: "SRC_READY_WAIT_ALL_DESTS",
    5: "SRC_READY_FWD_DATA"
}

src_state_map = {
    0: "SRC_IDLE",
    1: "SRC_REMOTE",
    2: "SRC_LOCAL",
    3: "SRC_ENDPOINT"
}

###############################################################################
# Reading registers
###############################################################################
def read_noc_status_register(loc, device, noc_id, reg_name):
    reg_addr = device.get_tensix_register_address(reg_name) + (noc_id * 0x10000)
    val = read_words_from_device(loc, reg_addr, device.id())[0]
    return val

###############################################################################
# Register Definitions and Extraction
###############################################################################
def get_noc_status_registers(loc, device, noc_id):
    register_groups = {
        "Transaction Counters (Sent)": {
            "nonposted write reqs sent"                       : "NIU_MST_NONPOSTED_WR_REQ_SENT",
            "posted write reqs sent"                          : "NIU_MST_POSTED_WR_REQ_SENT",
            "nonposted write words sent"                      : "NIU_MST_NONPOSTED_WR_DATA_WORD_SENT",
            "posted write words sent"                         : "NIU_MST_POSTED_WR_DATA_WORD_SENT",
            "write acks received"                             : "NIU_MST_WR_ACK_RECEIVED",
            "read reqs sent"                                  : "NIU_MST_RD_REQ_SENT",
            "read words received"                             : "NIU_MST_RD_DATA_WORD_RECEIVED",
            "read resps received"                             : "NIU_MST_RD_RESP_RECEIVED"
        },

        "Transaction Counters (Received)": {
            "nonposted write reqs received"                   : "NIU_SLV_NONPOSTED_WR_REQ_RECEIVED",
            "posted write reqs received"                      : "NIU_SLV_POSTED_WR_REQ_RECEIVED",
            "nonposted write words received"                  : "NIU_SLV_NONPOSTED_WR_DATA_WORD_RECEIVED",
            "posted write words received"                     : "NIU_SLV_POSTED_WR_DATA_WORD_RECEIVED",
            "write acks sent"                                 : "NIU_SLV_WR_ACK_SENT",
            "read reqs received"                              : "NIU_SLV_RD_REQ_RECEIVED",
            "read words sent"                                 : "NIU_SLV_RD_DATA_WORD_SENT",
            "read resps sent"                                 : "NIU_SLV_RD_RESP_SENT"
        },
    }

    noc_registers = {group_name: {} for group_name in register_groups.keys()}
    for group_name, registers in register_groups.items():
        for register_desc, reg_name in registers.items():
            noc_registers[group_name][register_desc] = read_noc_status_register(loc, device, noc_id, reg_name)
    return noc_registers

###############################################################################
# Rich Table Formatting Helpers
###############################################################################
def get_formatted_value_from_reg_info(reg_info: dict) -> str:
    reg_format = reg_info.get("format", "")
    raw_value = reg_info.get("value", "")
    if reg_format == "state":
        return reg_info.get("description", str(raw_value))
    elif reg_format == "hex":
        try:
            int_value = int(raw_value)
            return f"0x{int_value:08x}"
        except Exception:
            return str(raw_value)
    else:
        return str(raw_value)

def rich_create_group_table(group_name: str, registers: dict, simple_print) -> Table:
    """
    Creates a Rich Table for a given group of stream registers.
    Displays two columns: "Description" and "Value" (formatted accordingly).
    """
    table = Table(title=group_name, title_style="bold magenta")
    if simple_print:
        table.box = box.SIMPLE
        table.show_header=False

    table.add_column("Description", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    for reg_name, reg_info in registers.items():
        if isinstance(reg_info, dict):
            table.add_row(reg_name, get_formatted_value_from_reg_info(reg_info))
        else:
            table.add_row(reg_name, f"0x{reg_info:08x} ({reg_info:d})")
    return table

def print_grouped_table(regs: dict, grouping: List[List[str]], simple_print) -> None:
    """
    Uses a grouping specification to print stream registers.
    Each inner list is printed as a row (side-by-side via Rich Columns).
    If a group name is missing, a Panel with "<No data>" is shown.
    """
    if simple_print:
        # Transform grouping into single-column format for simple print mode
        grouping = simplify_grouping(grouping)

    for group_row in grouping:
        tables = []
        for group_name in group_row:
            if group_name in regs:
                tables.append(rich_create_group_table(group_name, regs[group_name], simple_print))
            else:
                tables.append(Panel("<No data>", title=group_name))
        console.print(Columns(tables, equal=True, expand=False))
        console.print()  # blank line

def simplify_grouping(grouping):
    # Transforms grouping into single-column format for simple print mode
    return [[group] for group in [item for sublist in grouping for item in sublist]]

###############################################################################
# Rich Print Status Registers
###############################################################################
def rich_print_noc_status_registers(loc, device, noc_id, simple_print=False):
    console.print(f"[bold]NOC{noc_id} Registers[/bold]")
    noc_registers = get_noc_status_registers(loc, device, noc_id)
    grouping = [
        ["Transaction Counters (Sent)", "Transaction Counters (Received)"],
    ]

    print_grouped_table(noc_registers, grouping, simple_print)


###############################################################################
# Dumping All NOC Registers
###############################################################################
def rich_dump_noc_status_registers(loc, device, simple_print=False):
    rich_print_noc_status_registers(loc, device, 0, simple_print)
    rich_print_noc_status_registers(loc, device, 1, simple_print)

###############################################################################
# Main Command Entry
###############################################################################
def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"]
    )

    if dopt.args["<noc-id>"]:
        try:
            noc_id = int(dopt.args["<noc-id>"])
        except ValueError:
            util.ERROR(f"Invalid NOC identifier: {dopt.args['<noc-id>']}")
            return []
        if noc_id not in [0, 1]:
            util.ERROR(f"Invalid NOC identifier: {noc_id}")
            return []
        noc_ids = [noc_id]
    else:
        noc_ids = [0, 1]

    simple_print = dopt.args["--simple"]

    # Iterate over selected devices, locations, and NOC identifiers
    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            console.print(f"[bold green]==== Device {device.id()} - Location: {loc.to_str('noc0')}[/bold green]")
            if dopt.args["status"]:
                for noc_id in noc_ids:
                    rich_print_noc_status_registers(loc, device, noc_id, simple_print)
            elif dopt.args["dump"]:
                rich_dump_noc_status_registers(loc, device, simple_print)
    return []
