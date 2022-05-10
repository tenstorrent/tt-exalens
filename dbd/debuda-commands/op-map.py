command_metadata = {
        "short" : "m",
        "expected_argument_count" : 0,
        "arguments_description" : ": draws a mini map of the current epoch"
    }

def run(args, context):
    for graph_name, graph in context.netlist.graphs.items():
        for op_name in graph.op_names():
            op = graph.root[op_name]
            print (f"{graph_name}/{op_name}: grid_loc: {op['grid_loc']}, grid_size: {op['grid_size']} ")
