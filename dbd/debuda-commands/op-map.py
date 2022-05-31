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
        for op_name in graph.op_names():
            op = graph.root[op_name]
            row = [ f"{graph_name}/{op_name}", op['type'], epoch_id, f"{graph.root['target_device']}", f"{op['grid_loc']}", f"{op['grid_size']}"]
            rows.append (row)

    print (tabulate(rows, headers = [ "Op", "Op type", "Epoch", "Device", "Grid Loc", "Grid Size" ]))

    return navigation_suggestions