from tabulate import tabulate

command_metadata = {
        "short" : "tt",
        "expected_argument_count" : 0,
        "arguments_description" : ": test only"
    }

def run(args, context, ui_state = None):
    navigation_suggestions = []

    current_device_id = ui_state["current_device_id"]
    current_device = context.devices[current_device_id]
    graph = context.netlist.graph(ui_state["current_graph_name"])

    a_pipe = list (graph.pipes)[0]
    a_buffer = list (graph.buffers)[0]
    an_op = list (graph.ops)[0]

    all_buffers = graph.get_buffers(graph.ops)
    if all_buffers != graph.buffers:
        all_buffers.compare (graph.buffers)

    for op_name in graph.op_names():
        op = graph.ops[op_name]
        b = graph.get_buffers(op)

        print (f"----- Before filter for {op_name}")
        print (b)
        print ("-- After filter")
        b.keep (graph.is_src_buffer)
        # b.keep (lambda x: not graph.is_src_buffer(x))
        # b.delete (graph.is_src_buffer)
        print (b)

    return navigation_suggestions