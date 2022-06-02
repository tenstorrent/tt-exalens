from tabulate import tabulate

command_metadata = {
        "short" : "om",
        "expected_argument_count" : 0,
        "arguments_description" : ": draws a mini map of the current epoch"
    }

def run(args, context, ui_state = None):
    navigation_suggestions = []

    rows = []
    for graph_name, graph in context.netlist.graphs.items():
        epoch_id = context.netlist.graph_name_to_epoch_id (graph_name)
        device_id = context.netlist.graph_name_to_device_id (graph_name)
        device = context.devices[device_id]
        for op_name in graph.op_names():
            op = graph.root[op_name]
            grid_loc = op['grid_loc']
            noc0_x, noc0_y = device.rc_to_noc0 (grid_loc[0], grid_loc[1])
            row = [ f"{graph_name}/{op_name}", op['type'], epoch_id, f"{graph.root['target_device']}", f"{grid_loc}", f"{noc0_x}-{noc0_y}", f"{op['grid_size']}"]
            rows.append (row)

    print (tabulate(rows, headers = [ "Op", "Op type", "Epoch", "Device", "Grid Loc", "NOC0 Loc", "Grid Size" ]))

    return navigation_suggestions