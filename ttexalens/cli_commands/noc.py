# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

"""
Usage:
    noc status [-d <device>] [--noc <noc-id>] [-l <loc>] [-s]
    noc dump [-d <device>] [-l <loc>] [-s]

Arguments:
    device-id         ID of the device [default: current active]
    noc-id            Identifier for the NOC (e.g. 0, 1) [default: both noc0 and noc1]
    loc               Location identifier (e.g. 0-0) [default: current active]

Options:
    -s, --simple     Print simple output

Description:
    Displays NOC (Network on Chip) registers.
        • "noc status" prints status registers for transaction counters.

Examples:
    noc status -d 0 -l 0,0                      # Prints status registers for device 0 on 0,0
    noc status -s                               # Prints status registers with simple output
"""

# Standard imports first
from typing import Dict, List, Optional

# Third-party imports
from docopt import docopt

# Local imports
from ttexalens import command_parser, util
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.tt_exalens_lib import read_words_from_device
from ttexalens.uistate import UIState
from ttexalens.rich_formatters import formatter, console

# Command metadata
command_metadata = {
    "short": "nc",
    "long": "noc",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc"],
}

###############################################################################
# Reading registers
###############################################################################
def read_noc_register(loc: OnChipCoordinate, device, noc_id: int, reg_name: str) -> int:
    """
    Read a NOC register value from the device.

    Args:
        loc: On-chip coordinate
        device: Device object
        noc_id: NOC identifier (0 or 1)
        reg_name: Register name

    Returns:
        Register value as integer
    """
    try:
        # Use device's method to get NOC register address
        reg_addr = device.get_noc_register_address(reg_name, noc_id)
        val = read_words_from_device(loc, reg_addr, device.id())[0]
        return val
    except Exception as e:
        util.ERROR(f"Failed to read register {reg_name} from NOC{noc_id}: {str(e)}")
        return 0


###############################################################################
# Register Definitions and Extraction
###############################################################################
def get_noc_status_registers(loc: OnChipCoordinate, device, noc_id: int) -> Dict[str, Dict[str, int]]:
    """
    Get all NOC status registers organized by groups.

    Args:
        loc: On-chip coordinate
        device: Device object
        noc_id: NOC identifier (0 or 1)

    Returns:
        Dictionary of register groups, each containing register values
    """
    register_groups = {
        "Transaction Counters (Sent)": {
            "nonposted write reqs sent": "NIU_MST_NONPOSTED_WR_REQ_SENT",
            "posted write reqs sent": "NIU_MST_POSTED_WR_REQ_SENT",
            "nonposted write words sent": "NIU_MST_NONPOSTED_WR_DATA_WORD_SENT",
            "posted write words sent": "NIU_MST_POSTED_WR_DATA_WORD_SENT",
            "write acks received": "NIU_MST_WR_ACK_RECEIVED",
            "read reqs sent": "NIU_MST_RD_REQ_SENT",
            "read words received": "NIU_MST_RD_DATA_WORD_RECEIVED",
            "read resps received": "NIU_MST_RD_RESP_RECEIVED",
        },
        "Transaction Counters (Received)": {
            "nonposted write reqs received": "NIU_SLV_NONPOSTED_WR_REQ_RECEIVED",
            "posted write reqs received": "NIU_SLV_POSTED_WR_REQ_RECEIVED",
            "nonposted write words received": "NIU_SLV_NONPOSTED_WR_DATA_WORD_RECEIVED",
            "posted write words received": "NIU_SLV_POSTED_WR_DATA_WORD_RECEIVED",
            "write acks sent": "NIU_SLV_WR_ACK_SENT",
            "read reqs received": "NIU_SLV_RD_REQ_RECEIVED",
            "read words sent": "NIU_SLV_RD_DATA_WORD_SENT",
            "read resps sent": "NIU_SLV_RD_RESP_SENT",
        },
    }

    noc_registers = {group_name: {} for group_name in register_groups.keys()}
    for group_name, registers in register_groups.items():
        for register_desc, reg_name in registers.items():
            noc_registers[group_name][register_desc] = read_noc_register(loc, device, noc_id, reg_name)
    return noc_registers


###############################################################################
# NOC Register Display Functions
###############################################################################
def display_noc_registers(loc: OnChipCoordinate, device, noc_id: int, simple_print: bool = False) -> None:
    """
    Display registers for a specific NOC.

    Args:
        loc: On-chip coordinate
        device: Device object
        noc_id: NOC identifier (0 or 1)
        simple_print: Whether to use simplified output format
    """
    formatter.print_header(f"NOC{noc_id} Registers", "bold")
    noc_registers = get_noc_status_registers(loc, device, noc_id)
    grouping = [
        ["Transaction Counters (Sent)", "Transaction Counters (Received)"],
    ]

    # Use the shared formatter API
    formatter.display_grouped_data(noc_registers, grouping, simple_print)


def display_all_noc_registers(loc: OnChipCoordinate, device, simple_print: bool = False) -> None:
    """
    Display registers for both NOCs.

    Args:
        loc: On-chip coordinate
        device: Device object
        simple_print: Whether to use simplified output format
    """
    display_noc_registers(loc, device, 0, simple_print)
    display_noc_registers(loc, device, 1, simple_print)


###############################################################################
# Main Command Entry
###############################################################################
def run(cmd_text: str, context: Dict, ui_state: Optional[UIState] = None) -> List:
    """
    Main entry point for the NOC command.

    Args:
        cmd_text: Command text from the user
        context: Command context
        ui_state: UI state object

    Returns:
        Empty list (convention for command handlers)
    """
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )

    # Parse and validate NOC ID
    if dopt.args["--noc"]:
        try:
            noc_id = int(dopt.args["--noc"])
            if noc_id not in [0, 1]:
                util.ERROR(f"Invalid NOC identifier: {noc_id}. Must be 0 or 1.")
                return []
            noc_ids = [noc_id]
        except ValueError:
            util.ERROR(f"Invalid NOC identifier: {dopt.args['--noc']}. Must be 0 or 1.")
            return []
    else:
        noc_ids = [0, 1]

    simple_print = dopt.args["--simple"]

    # Iterate over selected devices, locations, and NOC identifiers
    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            formatter.print_device_header(device, loc)

            if dopt.args["status"]:
                for noc_id in noc_ids:
                    display_noc_registers(loc, device, noc_id, simple_print)

    return []
