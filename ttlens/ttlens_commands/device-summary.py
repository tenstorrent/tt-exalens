# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  device [<device-id> [<axis-coordinate> [<cell-contents>]]]

Arguments:
  device-id            ID of the device [default: 0]
  axis-coordinate      Coordinate system for the axis [default: netlist]
                       Supported: netlist, noc0, noc1, nocTr, nocVirt, die, tensix
  cell-contents        A comma separated list of the cell contents [default: nocTr]
                       Supported:
                         riscv - show the status of the RISC-V ('R': running, '-': in reset)
                         block - show the type of the block at that coordinate
                         netlist, noc0, noc1, nocTr, nocVirt, die, tensix - show coordinate

Description:
  Shows a device summary. When no argument is supplied, shows the status of the RISC-V for all devices.

Examples:
  device                 # Shows the status of the RISC-V for all devices
  device 0 noc0          # Shows noc0 to nocTr mapping for device 0
  device 0 noc0 netlist  # Shows netlist coordinates in noc0 coordinages for device 0
"""  # Note: Limit the above comment to 100 characters in width

command_metadata = {
    "short": "d",
    "long": "device",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited", "metal"],
}

from docopt import docopt

from ttlens import tt_util as util
from ttlens.tt_coordinate import VALID_COORDINATE_TYPES
from ttlens.tt_lens_context import LimitedContext

def run(cmd_text, context, ui_state=None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    if args["<device-id>"]:
        device_id = int(args["<device-id>"])
        if device_id not in context.devices:
            util.ERROR(
                f"Invalid device ID ({device_id}). Valid devices IDs: {list(context.devices)}"
            )
            return []
        devices_list = [device_id]
    else:
        devices_list = list(context.devices.keys())

    axis_coordinate = args["<axis-coordinate>"] or "netlist"
    if axis_coordinate not in VALID_COORDINATE_TYPES:
        util.ERROR(
            f"Invalid axis coordinate type: {axis_coordinate}. Valid types: {VALID_COORDINATE_TYPES}"
        )
        return []

    cell_contents = ""
    if args["<cell-contents>"]:
        cell_contents = args["<cell-contents>"]
    elif isinstance(context, LimitedContext):
        cell_contents = "riscv"
    else:
        raise util.TTException(f"Invalid cell contents")

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
                if ct == "block":
                    block_type = device.get_block_type(loc)
                    cell_contents_str.append(block_type)
                elif ct == "riscv":
                    block_type = device.get_riscv_run_status(loc)
                    cell_contents_str.append(block_type)
                elif ct in VALID_COORDINATE_TYPES:
                    try:
                        coord_str = loc.to_str(ct)
                    except Exception as e:
                        coord_str = "N/A"
                    cell_contents_str.append(coord_str)
                else:
                    raise util.TTException(f"Invalid cell contents requested: '{ct}'")
            return ", ".join(cell_contents_str)

        print(
            device.render(
                legend=[],
                axis_coordinate=axis_coordinate,
                cell_renderer=cell_render_function,
            )
        )

    navigation_suggestions = []
    return navigation_suggestions
