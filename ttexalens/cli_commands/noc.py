# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

"""
Usage:
    noc status [-d <device>] [--noc <noc-id>] [-l <loc>] [-s]
    noc all [-d <device>] [-l <loc>] [-s]
    noc register (<reg-names> | --search <reg-pattern> [--max <max-regs>]) [-d <device>] [--noc <noc-id>] [-l <loc>] [-s]


Arguments:
    device-id         ID of the device [default: current active]
    noc-id            Identifier for the NOC (e.g. 0, 1) [default: both noc0 and noc1]
    loc               Location identifier (e.g. 0-0) [default: current active]
    reg-names         Name of specific NOC register(s) to display, can be comma-separated
    reg-pattern       Pattern in wildcard format for finding registers (mutually exclusive with <reg-names>)
    max-regs          Limit --search output (default: 10, use --max "all" to print all matches)


Options:
    -s, --simple            Print simple output


Description:
    Displays NOC (Network on Chip) registers.
        • "noc status" prints status registers for transaction counters.
        • "noc all" prints all registers.
        • "noc register <reg-names>" prints specific register(s) by name.
        • "noc register --search <reg-pattern>" searches through all registers with the given wildcard pattern.


Examples:
    noc status -d 0 -l 0,0                      # Prints status registers for device 0 on 0,0
    noc status -s                               # Prints status registers with simple output
    noc register NIU_MST_RD_REQ_SENT            # Prints a specific register value
    noc register NIU_MST_RD_REQ_SENT,NIU_MST_RD_DATA_WORD_RECEIVED  # Prints multiple registers
    noc register --search *_RD* --max all       # Show all registers that have "_RD" in their name
"""

# Third-party imports
from docopt import docopt

# Local imports
from ttexalens import command_parser, util
from ttexalens.util import search
from ttexalens.context import Context
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
from ttexalens.register_store import (
    NocConfigurationRegisterDescription,
    NocControlRegisterDescription,
    NocStatusRegisterDescription,
    RegisterDescription,
    RegisterStore,
)
from ttexalens.uistate import UIState
from ttexalens.rich_formatters import formatter

# Command metadata
command_metadata = {
    "short": "nc",
    "long": "noc",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc"],
}


def is_noc_register_description(description: RegisterDescription) -> bool:
    return isinstance(
        description,
        (NocStatusRegisterDescription, NocConfigurationRegisterDescription, NocControlRegisterDescription),
    )


def get_noc_register_names(register_store: RegisterStore) -> list[str]:
    """
    Get the names of all NOC registers from the register store.

    Args:
        register_store: The register store to query.

    Returns:
        A list of NOC register names.
    """
    return [
        name
        for name in register_store.get_register_names()
        if is_noc_register_description(register_store.get_register_description(name))
    ]


###############################################################################
# Register Definitions and Extraction
###############################################################################
def get_noc_status_registers(loc: OnChipCoordinate, device: Device, noc_id: int) -> dict[str, dict[str, int]]:
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

    register_store = device.get_block(loc).get_register_store(noc_id)
    noc_registers: dict[str, dict[str, int]] = {group_name: {} for group_name in register_groups.keys()}
    for group_name, registers in register_groups.items():
        for register_desc, reg_name in registers.items():
            noc_registers[group_name][register_desc] = register_store.read_register(reg_name)
    return noc_registers


def get_all_noc_registers(loc: OnChipCoordinate, device: Device) -> dict[str, dict[str, int]]:
    """
    Get all NOC registers for both NOC0 and NOC1.

    Args:
        loc: On-chip coordinate
        device: Device object

    Returns:
        Dictionary of all register values for both NOCs
    """
    noc_registers: dict[str, dict[str, int]] = {"Noc0 Registers": {}, "Noc1 Registers": {}}
    register_store_noc0 = device.get_block(loc).get_register_store(0)
    register_store_noc1 = device.get_block(loc).get_register_store(1)
    register_names = get_noc_register_names(register_store_noc0)  # We will get the same names for both NOCs
    for reg_name in register_names:
        noc_registers["Noc0 Registers"][reg_name] = register_store_noc0.read_register(reg_name)
        noc_registers["Noc1 Registers"][reg_name] = register_store_noc1.read_register(reg_name)
    return noc_registers


###############################################################################
# NOC Register Display Functions
###############################################################################
def display_noc_status_registers(
    loc: OnChipCoordinate, device: Device, noc_id: int, simple_print: bool = False
) -> None:
    """
    Display status registers for a specific NOC.

    Args:
        loc: On-chip coordinate
        device: Device object
        noc_id: NOC identifier (0 or 1)
        simple_print: Whether to use simplified output format
    """
    formatter.print_header(f"NOC{noc_id} Status Registers", "bold")
    noc_registers = get_noc_status_registers(loc, device, noc_id)
    grouping = [
        ["Transaction Counters (Sent)", "Transaction Counters (Received)"],
    ]

    # Use the shared formatter API
    formatter.display_grouped_data(noc_registers, grouping, simple_print)


def display_all_noc_registers(loc: OnChipCoordinate, device: Device, simple_print: bool = False) -> None:
    """
    Display all registers for both NOCs.

    Args:
        loc: On-chip coordinate
        device: Device object
        simple_print: Whether to use simplified output format
    """
    formatter.print_header("All NOC Registers", "bold")
    noc_registers = get_all_noc_registers(loc, device)

    # Get all register group names for grouping
    group_names = list(noc_registers.keys())
    grouping = [group_names]

    # Use the shared formatter API
    formatter.display_grouped_data(noc_registers, grouping, simple_print)


def display_all_noc_status_registers(loc: OnChipCoordinate, device: Device, simple_print: bool = False) -> None:
    """
    Display status registers for both NOCs.

    Args:
        loc: On-chip coordinate
        device: Device object
        simple_print: Whether to use simplified output format
    """
    display_noc_status_registers(loc, device, 0, simple_print)
    display_noc_status_registers(loc, device, 1, simple_print)


def display_specific_noc_registers(
    loc: OnChipCoordinate, device: Device, reg_names: list[str], noc_id: int, simple_print: bool = False
) -> None:
    """
    Display one or more specific NOC registers by name.

    Args:
        loc: On-chip coordinate
        device: Device object
        reg_names: List of register names to display
        noc_id: NOC identifier (0 or 1)
        simple_print: Whether to use simplified output format
    """
    # Get the list of valid register names
    register_store = device.get_block(loc).get_register_store(noc_id)
    valid_register_names = get_noc_register_names(register_store)

    # Create a data structure to hold register values
    register_data: dict[str, dict[str, int]] = {f"NOC{noc_id} Registers": {}}

    # Check if we have valid registers to display
    valid_registers_found = False
    invalid_registers = []

    # Process each requested register
    for reg_name in reg_names:
        reg_name = reg_name.strip()  # Remove any whitespace
        if not reg_name:  # Skip empty names
            continue

        if reg_name in valid_register_names:
            valid_registers_found = True
            # Read the register value
            value = register_store.read_register(reg_name)
            register_data[f"NOC{noc_id} Registers"][reg_name] = value
        else:
            invalid_registers.append(reg_name)

    # Report any invalid register names
    if invalid_registers:
        util.ERROR(f"The following register names are invalid for NOC{noc_id}: {', '.join(invalid_registers)}")

    # Only display if we found at least one valid register
    if valid_registers_found:
        # Display the registers
        formatter.display_grouped_data(register_data, [[f"NOC{noc_id} Registers"]], simple_print)
    elif not invalid_registers:
        # If no registers were found but none were invalid, it's likely an empty list
        util.ERROR(f"No register names provided for NOC{noc_id}")


###############################################################################
# Main Command Entry
###############################################################################
def run(cmd_text: str, context: Context, ui_state: UIState) -> list:
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
            noc_id = int(dopt.args["<noc-id>"])
            if noc_id not in (0, 1):
                util.ERROR(f"Invalid NOC identifier: {noc_id}. Must be 0 or 1.")
                return []
            noc_ids = [noc_id]
        except ValueError:
            util.ERROR(f"Invalid NOC identifier: {dopt.args['<noc-id>']}. Must be 0 or 1.")
            return []
    else:
        noc_ids = [0, 1]

    simple_print = dopt.args["--simple"]

    # Iterate over selected devices, locations, and NOC identifiers
    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            formatter.print_device_header(device, loc)

            if dopt.args["status"]:
                if dopt.args["--noc"]:
                    # If a specific NOC ID was specified, only display that one
                    display_noc_status_registers(loc, device, noc_ids[0], simple_print)
                else:
                    # Otherwise, display status for both NOCs
                    display_all_noc_status_registers(loc, device, simple_print)
            elif dopt.args["all"]:
                # Display all registers for both NOCs
                display_all_noc_registers(loc, device, simple_print)
            elif dopt.args["register"]:
                reg_names = []
                # Populate reg_names from either <reg-names> or <reg-pattern>, depending on the presence of --search
                if dopt.args["--search"]:
                    noc0_reg_store = device.get_block(loc).get_register_store(0)
                    all_reg_names = get_noc_register_names(noc0_reg_store)
                    max = dopt.args["<max-regs>"] if dopt.args["--max"] else 10
                    reg_names = search(all_reg_names, dopt.args["<reg-pattern>"], max)
                    if len(reg_names) == 0:
                        print("No matches found.")
                        return []

                else:
                    # Parse the comma-separated register names
                    reg_names_str = dopt.args["<reg-names>"]
                    reg_names = [name.strip() for name in reg_names_str.split(",")]

                if dopt.args["--noc"]:
                    # If a specific NOC ID was specified, only display for that one
                    print(f"Displaying registers for NOC{noc_ids[0]}: {', '.join(reg_names)}")
                    display_specific_noc_registers(loc, device, reg_names, noc_ids[0], simple_print)
                else:
                    # Otherwise, display for both NOCs
                    for noc_id in [0, 1]:
                        display_specific_noc_registers(loc, device, reg_names, noc_id, simple_print)

    return []
