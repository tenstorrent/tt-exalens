# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  device [<device-id> [<axis-coordinate> [<cell-contents>]]] [--no-legend]

Arguments:
  device-id            ID of the device [default: 0]
  axis-coordinate      Coordinate system for the axis [default: logical-tensix]
                       Supported: noc0, noc1, nocTr, nocVirt, die, logical-tensix, logical-eth, logical-dram
  cell-contents        A comma separated list of the cell contents [default: block]
                       Supported:
                         riscv - show the status of the RISC-V ('R': running, '-': in reset)
                         block - show the type of the block at that coordinate
                         netlist, noc0, noc1, nocTr, nocVirt, die - show coordinate

Description:
  Shows a device summary. When no argument is supplied, shows the status of the RISC-V for all devices.

Examples:
  device                           # Shows the status of the RISC-V for all devices
  device 0 noc0                    # Shows noc0 to nocTr mapping for device 0
  device 0 noc0 netlist            # Shows netlist coordinates in noc0 coordinages for device 0
  device 0 noc0 block --no-legend  # Shows the block type in noc0 coordinates for device 0 without the legend
"""  # Note: Limit the above comment to 100 characters in width

# TODO: Update docstring to reflect the actual command usage

command_metadata = {
    "short": "d",
    "long": "device",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited", "metal"],
}

from docopt import docopt

from ttlens import tt_util as util
from ttlens.tt_device import Device
from ttlens.tt_coordinate import VALID_COORDINATE_TYPES
from ttlens.tt_lens_context import LimitedContext


def color_block(text: str, block_type: str):
    color = Device.block_types[block_type]["color"]
    return f"{color}{text}{util.CLR_END}"


def run(cmd_text, context, ui_state=None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])
    dont_print_legend = args["--no-legend"]

    if args["<device-id>"]:
        device_id = int(args["<device-id>"])
        if device_id not in context.devices:
            util.ERROR(f"Invalid device ID ({device_id}). Valid devices IDs: {list(context.devices)}")
            return []
        devices_list = [device_id]
    else:
        devices_list = list(context.devices.keys())

    axis_coordinate = args["<axis-coordinate>"] or "logical-tensix"
    if axis_coordinate not in VALID_COORDINATE_TYPES or axis_coordinate == "netlist":
        util.ERROR(f"Invalid axis coordinate type: {axis_coordinate}. Valid types: {VALID_COORDINATE_TYPES}")
        return []

    cell_contents = ""
    if args["<cell-contents>"]:
        cell_contents = args["<cell-contents>"]
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

    for device_id in devices_list:
        device = context.devices[device_id]
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
                    text = device.get_riscv_run_status(loc)
                    cell_contents_str.append(color_block(text, block_type))
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
