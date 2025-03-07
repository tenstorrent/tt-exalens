# # SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  noc status [-d <device>] [-noc <noc-id>] [-l <loc>]
  noc stream <stream-id> [-d <device>] [-noc <noc-id>] [-l <loc>]
  noc dump [-d <device>] [-noc <noc-id>] [-l <loc>]

Arguments:
  device-id         ID of the device [default: current active]
  stream-id         ID of the stream to dump registers for
  noc-id            Identifier for the NOC (e.g. 0, 1) [default: both noc0 and noc1]
  loc               Location identifier (e.g. 0-0) [default: current active]

Description:
  Dumps NOC registers.
    • "noc status" prints status registers.
    • "noc stream <stream-id>" prints registers for a specific stream.
    • "noc dump" dumps a continuous block of registers.

Examples:
  noc status -d 0 -l 0,0                      # Prints status registers for device 0 on 0,0
  noc stream 3 -d 1 -noc 1                    # Prints stream 3 registers for device 1 on noc1
  noc dump                                    # Dumps all registers for device 0 on current core
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
def read_noc_status_register(loc, device_id, noc_id, reg_index):
    reg_addr = 0xFFB20000 + (noc_id * 0x10000) + 0x200 + (reg_index * 4)
    val = read_words_from_device(loc, reg_addr, device_id)[0]
    return val

def get_stream_reg_field(loc, device_id, stream_id, reg_index, start_bit, num_bits):
    reg_addr = 0xFFB40000 + (stream_id * 0x1000) + (reg_index * 4)
    val = read_words_from_device(loc, reg_addr, device_id)[0]
    mask = (1 << num_bits) - 1
    return (val >> start_bit) & mask

###############################################################################
# Register Definitions and Extraction
###############################################################################
def get_noc_status_registers(loc, device_id, noc_id):
    register_groups = {
        "Transaction Counters (Sent)": {
            "nonposted write reqs sent": 0xA,
            "posted write reqs sent": 0xB,
            "nonposted write words sent": 0x8,
            "posted write words sent": 0x9,
            "write acks received": 0x1,
            "read reqs sent": 0x5,
            "read words received": 0x3,
            "read resps received": 0x2
        },
        "Transaction Counters (Received)": {
            "nonposted write reqs received": 0x1A,
            "posted write reqs received": 0x1B,
            "nonposted write words received": 0x18,
            "posted write words received": 0x19,
            "write acks sent": 0x10,
            "read reqs received": 0x15,
            "read words sent": 0x13,
            "read resps sent": 0x12
        },
        "Router Port Status": {
            "router port x out vc full credit out vc stall": 0x24,
            "router port y out vc full credit out vc stall": 0x22,
            "router port niu out vc full credit out vc stall": 0x20
        },
        "Router Port X Debug": {
            "router port x VC14 & VC15 dbg": 0x3d,
            "router port x VC12 & VC13 dbg": 0x3c,
            "router port x VC10 & VC11 dbg": 0x3b,
            "router port x VC8 & VC9 dbg": 0x3a,
            "router port x VC6 & VC7 dbg": 0x39,
            "router port x VC4 & VC5 dbg": 0x38,
            "router port x VC2 & VC3 dbg": 0x37,
            "router port x VC0 & VC1 dbg": 0x36
        },
        "Router Port Y Debug": {
            "router port y VC14 & VC15 dbg": 0x35,
            "router port y VC12 & VC13 dbg": 0x34,
            "router port y VC10 & VC11 dbg": 0x33,
            "router port y VC8 & VC9 dbg": 0x32,
            "router port y VC6 & VC7 dbg": 0x31,
            "router port y VC4 & VC5 dbg": 0x30,
            "router port y VC2 & VC3 dbg": 0x2f,
            "router port y VC0 & VC1 dbg": 0x2e
        },
        "Router Port NIU Debug": {
            "router port niu VC6 & VC7 dbg": 0x29,
            "router port niu VC4 & VC5 dbg": 0x28,
            "router port niu VC2 & VC3 dbg": 0x27,
            "router port niu VC0 & VC1 dbg": 0x26
        }
    }
    noc_registers = {group_name: {} for group_name in register_groups.keys()}
    for group_name, registers in register_groups.items():
        for reg_name, reg_index in registers.items():
            noc_registers[group_name][reg_name] = read_noc_status_register(loc, device_id, noc_id, reg_index)
    return noc_registers

def get_stream_register_definitions():
    register_defs = {
        "Basic Stream Info": {
            "STREAM_ID": (224+5, 24, 6, "d"),
            "PHASE_AUTO_CFG_PTR": (12, 0, 24, "x"),
            "CURR_PHASE": (11, 0, 20, "d"),
            "CURR_PHASE_NUM_MSGS_REMAINING": (35, 0, 12, "d"),
            "NUM_MSGS_RECEIVED": (224+5, 0, 16, "d"),
            "NEXT_MSG_ADDR": (224+6, 0, 16, "x"),
            "NEXT_MSG_SIZE": (224+6, 16, 16, "x")
        },
        "Stream Control": {
            "OUTGOING_DATA_NOC": (10, 1, 1, "d"),
            "LOCAL_SOURCES_CONNECTED": (10, 3, 1, "d"),
            "SOURCE_ENDPOINT": (10, 4, 1, "d"),
            "REMOTE_SOURCE": (10, 5, 1, "d"),
            "RECEIVER_ENDPOINT": (10, 6, 1, "d"),
            "LOCAL_RECEIVER": (10, 7, 1, "d"),
            "REMOTE_RECEIVER": (10, 8, 1, "d"),
            "NEXT_PHASE_SRC_CHANGE": (10, 12, 1, "d"),
            "NEXT_PHASE_DST_CHANGE": (10, 13, 1, "d")
        },
        "Remote Source": {
            "INCOMING_DATA_NOC": (10, 0, 1, "d"),
            "REMOTE_SRC_X": (0, 0, 6, "d"),
            "REMOTE_SRC_Y": (0, 6, 6, "d"),
            "REMOTE_SRC_STREAM_ID": (0, 12, 6, "d"),
            "REMOTE_SRC_UPDATE_NOC": (10, 2, 1, "d"),
            "REMOTE_SRC_PHASE": (1, 0, 20, "d"),
            "REMOTE_SRC_DEST_INDEX": (0, 18, 6, "d"),
            "REMOTE_SRC_IS_MCAST": (10, 16, 1, "d")
        },
        "Remote Receiver": {
            "REMOTE_DEST_STREAM_ID": (2, 12, 6, "d"),
            "REMOTE_DEST_X": (2, 0, 6, "d"),
            "REMOTE_DEST_Y": (2, 6, 6, "d"),
            "REMOTE_DEST_BUF_START": (3, 0, 16, "d"),
            "REMOTE_DEST_BUF_SIZE": (4, 0, 16, "d"),
            "REMOTE_DEST_BUF_WR_PTR": (5, 0, 16, "d"),
            "REMOTE_DEST_MSG_INFO_WR_PTR": (9, 0, 16, "d"),
            "DEST_DATA_BUF_NO_FLOW_CTRL": (10, 15, 1, "d"),
            "MCAST_EN": (13, 12, 1, "d"),
            "MCAST_END_X": (13, 0, 6, "d"),
            "MCAST_END_Y": (13, 6, 6, "d"),
            "MCAST_LINKED": (13, 13, 1, "d"),
            "MCAST_VC": (13, 14, 1, "d"),
            "MCAST_DEST_NUM": (15, 0, 16, "d")
        },
        "Local Sources": {
            "LOCAL_SRC_MASK_LO": (48, 0, 32, "x"),
            "LOCAL_SRC_MASK_HI": (49, 0, 32, "x"),
            "MSG_ARB_GROUP_SIZE": (13, 16, 3, "d"),
            "MSG_SRC_IN_ORDER_FWD": (13, 19, 1, "d"),
            "STREAM_MSG_SRC_IN_ORDER_FWD_NUM_MSGS_REG_INDEX": (14, 0, 24, "d")
        },
        "Buffer Control": {
            "BUF_START": (6, 0, 16, "x"),
            "BUF_SIZE": (7, 0, 16, "x"),
            "BUF_RD_PTR": (23, 0, 16, "x"),
            "BUF_WR_PTR": (24, 0, 16, "x"),
            "MSG_INFO_PTR": (8, 0, 16, "x"),
            "MSG_INFO_WR_PTR": (25, 0, 16, "x"),
            "STREAM_BUF_SPACE_AVAILABLE_REG_INDEX": (27, 0, 16, "x"),
            "DATA_BUF_NO_FLOW_CTRL": (10, 14, 1, "d"),
            "UNICAST_VC_REG": (10, 18, 3, "d"),
            "REG_UPDATE_VC_REG": (10, 21, 3, "d")
        },
        "Scratch Registers": {
            **{f"SCRATCH_REG{i}": (248 + i, 0, 32, "x") for i in range(6)}
        },
        "Debug": {
            **{f"DEBUG_STATUS[{i}]": (224 + i, 0, 32, "x") for i in range(7)},
            **{"DEBUG_STATUS[7]": {
                "PHASE_STATE": (224 + 7, 0, 4, "state", phase_state_map),
                "SRC_READY_STATE": (224 + 7, 4, 3, "state", src_ready_state_map),
                "DEST_READY_STATE": (224 + 7, 7, 3, "state", dest_ready_state_map),
                "SRC_SIDE_PHASE_COMPLETE": (224 + 7, 10, 1, "d", {"0": "Not complete", "1": "Complete"}),
                "DEST_SIDE_PHASE_COMPLETE": (224 + 7, 11, 1, "d", {"0": "Not complete", "1": "Complete"}),
                "SRC_STATE": (224 + 7, 16, 4, "state", src_state_map),
                "DEST_STATE": (224 + 7, 20, 3, "state", dest_state_map)
            }},
            **{f"DEBUG_STATUS[{i}]": (224 + i, 0, 32, "x") for i in range(8, 10)}
        }
    }
    return register_defs

def get_stream_registers(loc, device_id, stream_id):
    register_defs = get_stream_register_definitions()
    stream_registers = {group_name: {} for group_name in register_defs.keys()}

    for group_name, registers in register_defs.items():
        if group_name != "Debug":
            for reg_name, reg_def in registers.items():
                reg_index, start_bit, num_bits = reg_def[0:3]
                format_type = reg_def[3]
                value = get_stream_reg_field(loc, device_id, stream_id, reg_index, start_bit, num_bits)
                reg_info = {"value": value}
                if format_type == "x":
                    reg_info["format"] = "hex"
                else:
                    reg_info["format"] = "dec"
                if len(reg_def) > 4:
                    state_desc = reg_def[4]
                else:
                    state_desc = ""
                if str(value) in state_desc:
                    reg_info["description"] = state_desc[str(value)]
                stream_registers[group_name][reg_name] = reg_info
        else:
            for reg_name, reg_def in registers.items():
                if isinstance(reg_def, list):  # if debug regs come as a list (if applicable)
                    for i, def_tuple in enumerate(reg_def):
                        reg_index, start_bit, num_bits, format_type = def_tuple
                        value = get_stream_reg_field(loc, device_id, stream_id, reg_index, start_bit, num_bits)
                        reg_num = int((reg_index - 224) % 10)
                        stream_registers[group_name][f"DEBUG_STATUS[{reg_num}]"] = {
                            "value": value,
                            "format": format_type
                        }
                elif isinstance(reg_def, tuple):  # standard tuple: process as normal register
                    reg_index, start_bit, num_bits, format_type = reg_def
                    value = get_stream_reg_field(loc, device_id, stream_id, reg_index, start_bit, num_bits)
                    stream_registers[group_name][reg_name] = {
                        "value": value,
                        "format": format_type
                    }
                elif isinstance(reg_def, dict):  # special case (e.g., DEBUG_STATUS[7])
                    for field_name, field_def in reg_def.items():
                        reg_index, start_bit, num_bits, format_type, state_map = field_def
                        value = get_stream_reg_field(loc, device_id, stream_id, reg_index, start_bit, num_bits)
                        stream_registers[group_name][field_name] = {
                            "value": value,
                            "format": format_type,
                            "description": state_map.get(value) if format_type == "state" else None,
                            "state_map": state_map if format_type == "state" else None
                        }
    return stream_registers

###############################################################################
# Rich Table Formatting Helpers for Stream Registers
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

def rich_create_group_table(group_name: str, registers: dict) -> Table:
    """
    Creates a Rich Table for a given group of stream registers.
    Displays two columns: "Register" and "Value" (formatted accordingly).
    """
    table = Table(title=group_name, title_style="bold magenta")
    table.add_column("Register", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")
    for reg_name, reg_info in registers.items():
        if isinstance(reg_info, dict):
            table.add_row(reg_name, get_formatted_value_from_reg_info(reg_info))
        else:
            table.add_row(reg_name, f"0x{reg_info:08x} ({reg_info:d})")
    return table

def print_grouped_table(stream_regs: dict, grouping: List[List[str]]) -> None:
    """
    Uses a grouping specification to print stream registers.
    Each inner list is printed as a row (side-by-side via Rich Columns).
    If a group name is missing, a Panel with "<No data>" is shown.
    """
    for group_row in grouping:
        tables = []
        for group_name in group_row:
            if group_name in stream_regs:
                tables.append(rich_create_group_table(group_name, stream_regs[group_name]))
            else:
                tables.append(Panel("<No data>", title=group_name))
        console.print(Columns(tables, equal=True, expand=False))
        console.print()  # blank line

###############################################################################
# Rich Print Status Registers
###############################################################################
def rich_print_noc_status_registers(loc, device_id, noc_id):
    console.print(f"[bold]NOC{noc_id} Registers[/bold]")
    noc_registers = get_noc_status_registers(loc, device_id, noc_id)
    grouping = [
        ["Transaction Counters (Sent)", "Transaction Counters (Received)"],
        ["Router Port Status", "Router Port NIU Debug"],
        ["Router Port X Debug", "Router Port Y Debug"]
    ]
    print_grouped_table(noc_registers, grouping)

###############################################################################
# Print Stream Registers
###############################################################################
def rich_print_noc_stream_registers(loc, device_id, stream_id):
    console.print(f"[bold]Stream {stream_id} Registers[/bold]")
    stream_regs = get_stream_registers(loc, device_id, stream_id)
    grouping = [
        ["Basic Stream Info", "Stream Control", "Buffer Control"],
        ["Remote Receiver", "Remote Source", "Local Sources"],
        ["Debug", "Scratch Registers"]
    ]
    print_grouped_table(stream_regs, grouping)

###############################################################################
# Dumping All NOC Registers
###############################################################################
def rich_dump_all_noc_registers(loc, device_id):
    for i in range(0, 64):
        rich_print_noc_stream_registers(loc, device_id, i)
    rich_print_noc_status_registers(loc, device_id, 0)
    rich_print_noc_status_registers(loc, device_id, 1)

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

    # Iterate over selected devices, locations, and NOC identifiers
    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            console.print(f"[bold green]==== Device {device.id()} - Location: {loc.to_str('noc0')}[/bold green]")
            if dopt.args["status"]:
                for noc_id in noc_ids:
                    rich_print_noc_status_registers(loc, device.id(), noc_id)
            elif dopt.args["stream"]:
                stream_id = int(dopt.args["<stream-id>"])
                rich_print_noc_stream_registers(loc, device.id(), stream_id)
            elif dopt.args["dump"]:
                rich_dump_all_noc_registers(loc, device.id())
    return []
