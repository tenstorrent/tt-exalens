from tabulate import tabulate

command_metadata = {
        "short" : "om",
        "expected_argument_count" : 0,
        "arguments_description" : ": draws a mini map of the current epoch"
    }

def run(args, context, ui_state = None):
    rows = []
    navigation_suggestions = []

    for graph_name, graph in context.netlist.graphs.items():
        for op_name in graph.op_names():
            op = graph.root[op_name]
            print (f"{graph_name}/{op_name}: grid_loc: {op['grid_loc']}, grid_size: {op['grid_size']} ")
            row = [ f"{graph_name}/{op_name}", f"{op['grid_loc']}", f"{op['grid_size']}"]
            rows.append (row)

    print (tabulate(rows, headers = [ "Op", "Grid Loc", "Grid Size" ]))

    return navigation_suggestions