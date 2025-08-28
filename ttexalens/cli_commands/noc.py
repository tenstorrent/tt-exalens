# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC
# SPDX-License-Identifier: Apache-2.0

"""
Usage:
    noc status [-d <device>] [--noc <noc-id>] [-l <loc>] [-s]
    noc all [-d <device>] [-l <loc>] [-s]
    noc register (<reg-names> | --search <reg-pattern> [--max <max-regs>]) [-d <device>] [--noc <noc-id>] [-l <loc>] [-s]
    noc vc-stall [-d <device>] [--noc <noc-id>]

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
    noc vc-stall -d 0 --noc 1                   # Identify stalled VC on NoC 1
"""

# Third-party imports
from docopt import docopt
from typing import List, Optional, Set, Tuple

# Local imports
from ttexalens import command_parser, util
from ttexalens.tt_exalens_lib import read_word_from_device
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
def read_register_with_address(register_store: RegisterStore, reg_name: str) -> tuple[str, int, int]:
    """
    Read a register and return its name, address, and value.

    Args:
        register_store: The register store to read from
        reg_name: Name of the register to read

    Returns:
        Tuple containing (name, address, value)
    """
    desc = register_store.get_register_description(reg_name)
    address = desc.noc_address if desc.noc_address is not None else 0
    value = register_store.read_register(reg_name)
    return (reg_name, address, value)


def get_noc_status_registers(
    loc: OnChipCoordinate, device: Device, noc_id: int
) -> dict[str, list[tuple[str, int, int]]]:
    """
    Get all NOC status registers organized by groups.

    Args:
        loc: On-chip coordinate
        device: Device object
        noc_id: NOC identifier (0 or 1)

    Returns:
        Dictionary of register groups, each containing list of (name, address, value) tuples
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
    noc_registers: dict[str, list[tuple[str, int, int]]] = {group_name: [] for group_name in register_groups.keys()}
    for group_name, registers in register_groups.items():
        for register_desc, reg_name in registers.items():
            name, address, value = read_register_with_address(register_store, reg_name)
            noc_registers[group_name].append((register_desc, address, value))
    return noc_registers


def get_all_noc_registers(loc: OnChipCoordinate, device: Device) -> dict[str, list[tuple[str, int, int]]]:
    """
    Get all NOC registers for both NOC0 and NOC1.

    Args:
        loc: On-chip coordinate
        device: Device object

    Returns:
        Dictionary of all register values for both NOCs
    """
    register_store_noc0 = device.get_block(loc).get_register_store(0)
    register_names = get_noc_register_names(register_store_noc0)  # We will get the same names for both NOCs

    registers = {}
    registers["Noc0 Registers"] = get_noc_registers(device, loc, 0, register_names)
    registers["Noc1 Registers"] = get_noc_registers(device, loc, 1, register_names)

    return registers


def get_noc_registers(
    device: Device, loc: OnChipCoordinate, noc_id: int, register_names: list[str]
) -> list[tuple[str, int, int]]:
    """
    Get NOC register values with their addresses.

    Args:
        device: Device object
        loc: On-chip coordinate
        noc_id: NOC identifier (0 or 1)
        register_names: List of register names to read

    Returns:
        List of tuples containing (name, address, value)
    """
    register_store = device.get_block(loc).get_register_store(noc_id)
    result = []
    for name in register_names:
        result.append(read_register_with_address(register_store, name))
    return result


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
    display_grouped_data(noc_registers, grouping, simple_print)


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
    display_grouped_data(noc_registers, grouping, simple_print)


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

    # Filter and validate register names
    valid_registers = []
    invalid_registers = []

    for reg_name in reg_names:
        reg_name = reg_name.strip()  # Remove any whitespace
        if not reg_name:  # Skip empty names
            continue

        if reg_name in valid_register_names:
            valid_registers.append(reg_name)
        else:
            invalid_registers.append(reg_name)

    # Report any invalid register names
    if invalid_registers:
        util.ERROR(f"The following register names are invalid for NOC{noc_id}: {', '.join(invalid_registers)}")

    # Only display if we found at least one valid register
    if valid_registers:
        register_data = {f"NOC{noc_id} Registers": get_noc_registers(device, loc, noc_id, valid_registers)}
        display_grouped_data(register_data, [[f"NOC{noc_id} Registers"]], simple_print)
    elif not invalid_registers:
        # If no registers were found but none were invalid, it's likely an empty list
        util.ERROR(f"No register names provided for NOC{noc_id}")


def display_grouped_data(
    data: dict[str, list[tuple[str, int, int]]], grouping: list[list[str]], simple_print: bool = False
) -> None:
    """
    Display grouped data in a formatted way.

    Args:
        data: Dictionary containing the data to display
        grouping: List of groups for display organization
        simple_print: Whether to use simplified output format
    """
    columns = [("Name", ""), ("Address", ""), ("Value", "")]

    # Transform the data to convert integers to hex strings and sort by address
    transformed_data = {}
    for group_name, rows in data.items():
        # Sort by address first (using original int values)
        sorted_rows = sorted(rows, key=lambda x: x[1])  # Sort by address (second element)

        transformed_rows = []
        for row in sorted_rows:
            # Convert each tuple (str, int, int) to (str, str, str) with hex values
            name, addr, value = row
            transformed_row = (name, f"0x{addr:08x}", f"0x{value:08x}")
            transformed_rows.append(transformed_row)
        transformed_data[group_name] = transformed_rows

    formatter.display_grouped_data(transformed_data, columns, grouping=grouping, simple_print=simple_print)


###############################################################################
# NOC Helper functions
###############################################################################
def _get_invalid_bits(expected_value, real_value):
    diff = expected_value ^ real_value
    invalid_bits = []
    for i in range(32):
        if diff & (1 << i):
            invalid_bits.append(i)
    return invalid_bits


def _get_worker_locations_and_grid_size(device: Device) -> Tuple[List[OnChipCoordinate], int, int]:
    """Get all functional worker locations and determine grid dimensions."""
    worker_locations = []
    num_rows = 0
    num_cols = 0

    for block_loc in device.get_block_locations(block_type="functional_workers"):
        worker_locations.append(block_loc)
        logical_coords = block_loc.to("logical")[0]
        num_rows = max(num_rows, logical_coords[0])
        num_cols = max(num_cols, logical_coords[1])

    return worker_locations, num_rows, num_cols


def _calculate_next_coordinate(
    current_worker: OnChipCoordinate,
    direction_index: int,
    noc_id: int,
    num_rows: int,
    num_cols: int,
    device: Device,
    direction_vectors: dict,
) -> Optional[OnChipCoordinate]:
    """Calculate the next coordinate to visit based on error direction."""
    current_logical = current_worker.to("logical")[0]
    core_type = current_worker.to("logical")[1]

    if direction_index == 0:  # Y-direction error
        next_x = current_logical[1]
        next_y = current_logical[0] + direction_vectors["y"][noc_id]
    else:  # X-direction error
        next_x = current_logical[1] + direction_vectors["x"][noc_id]
        next_y = current_logical[0]

    try:
        return OnChipCoordinate(next_y % num_rows, next_x % num_cols, "logical", device, core_type)
    except Exception as e:
        util.VERBOSE(f"Could not move to ({next_x},{next_y}): {e}")
        return None


def _find_stalled_vc_for_noc(
    worker_locations: List[OnChipCoordinate],
    device: Device,
    noc_id: int,
    num_rows: int,
    num_cols: int,
    base_address: int,
    vc_register_offsets: List[int],
    expected_vc_value: int,
    direction_vectors: dict,
) -> Tuple[int, Optional[OnChipCoordinate]]:
    """Find stalled VC and problem core for a specific NOC."""
    problem_vc = -1
    problem_core = None
    last_invalid = None
    visited: Set[OnChipCoordinate] = set()

    for worker_coordinates in worker_locations:
        if problem_core:
            break

        to_visit: Set[OnChipCoordinate] = set()
        if worker_coordinates not in visited:
            to_visit.add(worker_coordinates)

        while to_visit and not problem_core:
            current_worker = to_visit.pop()
            visited.add(current_worker)
            current_worker_has_error = False

            for direction_index, offset in enumerate(vc_register_offsets):
                reg_addr = base_address + offset
                vc_value = read_word_from_device(
                    current_worker, reg_addr, noc_id ^ 1
                )  # Use the other NoC to read the value

                if vc_value != expected_vc_value:
                    invalid_bits_upper = _get_invalid_bits(expected_vc_value >> 16, vc_value >> 16)
                    problem_vc = invalid_bits_upper[0]
                    current_worker_has_error = True

                    next_coord = _calculate_next_coordinate(
                        current_worker, direction_index, noc_id, num_rows, num_cols, device, direction_vectors
                    )
                    if next_coord:
                        to_visit.add(next_coord)

            if not current_worker_has_error and last_invalid:
                problem_core = last_invalid
                last_invalid = None
            if current_worker_has_error:
                last_invalid = current_worker

    return problem_vc, problem_core


def identify_stalled_vc(loc: OnChipCoordinate, device: Device, noc_ids: List[int]) -> None:
    """
    Identify stalled virtual channels on specified NOCs.

    This function traverses the chip grid to find VC stalls by reading VC status registers
    and following the direction of errors to identify the source of the stall.

    Args:
        loc: On-chip coordinate (currently unused but kept for API consistency)
        device: Device object to query
        noc_ids: List of NOC IDs to check (0 and/or 1)
    """
    # VC stall detection constants
    noc_base_addresses = [0xFFB20300, 0xFFB30300]  # NIU_BASE for NoC0, NIU_BASE for NoC1
    vc_register_offsets = [0x00000008, 0x00000010]  # Y and X direction VC data
    expected_vc_value = 0xFFFF0000
    direction_vectors = {
        "x": [1, -1],  # X direction movement for NOC0, NOC1
        "y": [1, -1],  # Y direction movement for NOC0, NOC1
    }

    worker_locations, num_rows, num_cols = _get_worker_locations_and_grid_size(device)

    for noc_id in noc_ids:
        problem_vc, problem_core = _find_stalled_vc_for_noc(
            worker_locations,
            device,
            noc_id,
            num_rows,
            num_cols,
            noc_base_addresses[noc_id],
            vc_register_offsets,
            expected_vc_value,
            direction_vectors,
        )

        if problem_vc == -1:
            util.INFO(f"No VC is stalled on NOC{noc_id}")
        else:
            util.INFO(f"VC {problem_vc} is stalled at core {problem_core} on NOC{noc_id}")


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
            elif dopt.args["vc-stall"]:
                identify_stalled_vc(loc, device, noc_ids)
    return []
