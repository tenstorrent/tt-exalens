"""
Usage:
  device [<device-id> [<axis-coordinate> [<cell-contents>]]]

Arguments:
  device-id            ID of the device [default: 0]
  axis-coordinate      Coordinate system for the axis [default: netlist]
                       Supported: netlist, noc0, noc1, nocTr, nocVirt, die, tensix
  cell-contents        A comma separated list of the cell contents [default: op]
                       Supported:
                         op - show operation details
                         netlist, noc0, noc1, nocTr, nocVirt, die, tensix - show coordinate

Shows a device summary. When no argument is supplied, it iterates through all devices used by the
currently loaded netlist.

Examples:
  device                 Shows op mapping for all devices
  device 0 noc0          Shows op mapping in noc0 coordinates for device 0
  device 0 netlist noc0  Shows netlist to noc0 mapping for device 0
""" # Limit above to 100 characters in width

command_metadata = {
    "short": "d",
    "long": "device",
    "type": "high-level",
    "description": __doc__
}

import tt_util as util
from tt_coordinate import VALID_COORDINATE_TYPES
from docopt import docopt

def run(cmd_text, context, ui_state=None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])

    if args["<device-id>"]:
        device_id = int(args["<device-id>"])
        if device_id not in context.devices:
            util.ERROR(f"Invalid device ID ({device_id}). Valid devices IDs: {list(context.devices)}")
            return []
        devices_list = [device_id]
    else:
        devices_list = list(context.devices.keys())

    axis_coordinate = args["<axis-coordinate>"] or "netlist"
    if axis_coordinate not in VALID_COORDINATE_TYPES:
        util.ERROR(f"Invalid axis coordinate type: {axis_coordinate}. Valid types: {VALID_COORDINATE_TYPES}")
        return []

    cell_contents = args["<cell-contents>"] or "op"

    for device_id in devices_list:
        device = context.devices[device_id]
        util.INFO (f"==== Device {device.id()}")

        func_workers = device.get_block_locations (block_type = "functional_workers")

        loc_to_epoch = {}
        for loc in func_workers:
            loc_to_epoch[loc] = device.get_epoch_id(loc)

        epoch_ids = list (set (loc_to_epoch.values()))
        epoch_ids.sort()
        if len(epoch_ids) > 1:
            util.WARN (f"Device {device_id} has functional workers in multiple epochs: {epoch_ids}")

        graph_name = context.netlist.get_graph_name(epoch_ids[0], device_id)
        graph = context.netlist.graph(graph_name)
        op_list = list (graph.ops.keys())
        op_color_map = { op_name : util.clr_by_index(i) for i, op_name in enumerate(op_list) }

        def cell_render_function(loc):
            s = []
            if loc in func_workers:
                for ct in cell_contents.split(','):
                    ct = ct.strip()
                    if ct == "op":
                        epoch_id = device.get_epoch_id(loc)
                        epoch_id = 0
                        graph_name = context.netlist.get_graph_name(epoch_id, device_id)
                        graph = context.netlist.graph(graph_name)
                        op_name = graph.location_to_op_name(loc)
                        if op_name:
                            s.append(f"{op_color_map[op_name]}{op_name} ({loc_to_epoch[loc]}){util.CLR_END}")
                    elif ct in VALID_COORDINATE_TYPES:
                        coord_str = loc.to_str (ct)
                        s.append (coord_str)
                    else:
                        util.ERROR (f"Invalid cell contents requested: {ct}")
                return ", ".join(s)
            return ""

        print(device.render (legend=[], axis_coordinate=axis_coordinate, cell_renderer=cell_render_function))

    navigation_suggestions = []
    return navigation_suggestions