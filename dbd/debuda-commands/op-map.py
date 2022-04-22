command_metadata = {
        "short" : "m",
        "expected_argument_count" : 0,
        "arguments_description" : ": draws a mini map of the current epoch"
    }

def run(args, globals):
    for graph_name in globals["NETLIST"]["graphs"].keys():
        graph = globals["NETLIST"]["graphs"][graph_name]
        for op_name in graph.keys():
            if op_name not in ['target_device', 'input_count']:
                op = graph[op_name]
                print (f"{graph_name}/{op_name}: grid_loc: {op['grid_loc']}, grid_size: {op['grid_size']} ")
