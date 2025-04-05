# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  device [-d <device-id>] [<axis-coordinate> [<cell-contents>]] [--no-legend]

Arguments:
  device-id            ID of the device [default: all]
  axis-coordinate      Coordinate system for the axis [default: logical-tensix]
                       Supported: noc0, noc1, translated, virtual, die, logical-tensix, logical-eth, logical-dram
  cell-contents        A comma separated list of the cell contents [default: block]
                       Supported:
                         riscv - show the status of the RISC-V ('R': running, '-': in reset)
                         block - show the type of the block at that coordinate
                         logical, noc0, noc1, translated, virtual, die - show coordinate
                         noc0_id - show the NOC0 node ID (x-y) for the block
                         noc1_id - show the NOC1 node ID (x-y) for the block (if there is no noc1 block, it will show empty)

Description:
  Shows a device summary. When no argument is supplied, shows the status of the RISC-V for all devices.

Examples:
  device                              # Shows the status of the RISC-V for all devices
  device noc0                         # Shows the status of the RISC-V on noc0 axis for all devices
  device logical-tensix noc0          # Shows noc0 coordinates on logical tensix axis for all devices
  device noc0 block --no-legend       # Shows the block type in noc0 axis for all devices without legend
  device -d 0 die                     # Shows the status of the RISC-V on die axis for device 0
  device -d 0 logical-dram noc0       # Shows noc0 coordinates on logical dram axis for device 0
  device -d 0 noc0 block --no-legend  # Shows the block type on noc0 axis for device 0 without legend
"""  # Note: Limit the above comment to 120 characters in width

command_metadata = {
    "short": "d",
    "long": "device",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device"],
}

from docopt import docopt

from ttexalens import command_parser, util as util
from ttexalens.device import Device
from ttexalens.coordinate import VALID_COORDINATE_TYPES, OnChipCoordinate
from ttexalens.context import LimitedContext
from ttexalens.tt_exalens_lib import read_words_from_device


def color_block(text: str, block_type: str):
    color = Device.block_types[block_type]["color"]
    return f"{color}{text}{util.CLR_END}"


def get_riscv_run_status(device: Device, location: OnChipCoordinate) -> str:
    """
    Returns the riscv soft reset status as a string of 4 characters one for each riscv core.
    '-' means the core is in reset, 'R' means the core is running.
    """
    risc_names = device.get_risc_names_for_location(location)
    block_type = device.get_block_type(location)
    if block_type == "functional_workers":
        status_str = ""
        for risc_name in risc_names:
            risc_debug = device.get_risc_debug(location, risc_name)
            status_str += "-" if risc_debug.is_in_reset() else "R"
        return status_str
    if block_type == "harvested_workers":
        return "----"
    return block_type


def run(cmd_text, context, ui_state=None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )
    dont_print_legend = dopt.args["--no-legend"]
    axis_coordinate = dopt.args["<axis-coordinate>"] or "logical-tensix"
    valid_axis_types = [coord for coord in VALID_COORDINATE_TYPES if coord != "logical"]
    if axis_coordinate not in valid_axis_types:
        util.ERROR(f"Invalid axis coordinate type: {axis_coordinate}. Valid types: {valid_axis_types}")
        return []

    if not dopt.args["-d"]:
        dopt.args["-d"] = "all"

    cell_contents = ""
    if dopt.args["<cell-contents>"]:
        cell_contents = dopt.args["<cell-contents>"]
    elif isinstance(context, LimitedContext):
        cell_contents = "riscv"
    else:
        raise util.TTException(f"Invalid cell contents")

    # Create a legend
    if not dont_print_legend:

        def print_legend(line):
            print(util.CLR_INFO + line + util.CLR_END)

        print_legend("")
        print_legend(f"Legend:")
        print_legend(f"  Axis coordinates: {axis_coordinate}")
        print_legend(f"  Cell contents: {cell_contents}")
        if "riscv" in cell_contents:
            print_legend(f"    riscv - show the status of the RISC-V ('R': running, '-': in reset)")
        if "block" in cell_contents:
            print_legend(f"    block - show the type of the block at that coordinate")
        print_legend(f"  Colors:")
        if axis_coordinate == "logical-tensix":
            print_legend(f"    {color_block('functional_workers', 'functional_workers')}")
        elif axis_coordinate == "logical-eth":
            print_legend(f"    {color_block('eth', 'eth')}")
        elif axis_coordinate == "logical-dram":
            print_legend(f"    {color_block('dram', 'dram')}")
        else:
            for block_type in Device.block_types:
                print_legend(f"    {color_block(block_type, block_type)}")
        print_legend("")

    device: Device
    for device in dopt.for_each("--device", context, ui_state):
        jtag_prompt = "JTAG" if ui_state.current_device._has_jtag else ""
        util.INFO(f"==== Device {jtag_prompt}{device.id()}")

        # What to render in each cell
        cell_contents_array = [s.strip() for s in cell_contents.split(",")]

        def cell_render_function(loc):
            # One string for each of cell_contents_array elements
            cell_contents_str = []

            for ct in cell_contents_array:
                block_type = device.get_block_type(loc)
                if ct == "block":
                    cell_contents_str.append(color_block(block_type, block_type))
                elif ct == "riscv":
                    text = get_riscv_run_status(device, loc)
                    cell_contents_str.append(color_block(text, block_type))
                elif ct == "noc0_id" or ct == "noc1_id":
                    noc_id = 0 if ct == "noc0_id" else 1
                    try:
                        noc_node_id = device.get_register_store(loc, noc_id=noc_id).read_register("NOC_NODE_ID")
                        x = noc_node_id & 0x3F
                        y = (noc_node_id >> 6) & 0x3F
                        cell_contents_str.append(color_block(f"{x:02}-{y:02}", block_type))
                    except:
                        cell_contents_str.append("")
                elif ct in VALID_COORDINATE_TYPES:
                    try:
                        coord_str = loc.to_str(ct)
                    except Exception as e:
                        coord_str = "N/A"
                    cell_contents_str.append(color_block(coord_str, block_type))
                else:
                    raise util.TTException(f"Invalid cell contents requested: '{ct}'")
            return ", ".join(cell_contents_str)

        print(
            device.render(
                legend=None,
                axis_coordinate=axis_coordinate,
                cell_renderer=cell_render_function,
            )
        )

    navigation_suggestions = []
    return navigation_suggestions
