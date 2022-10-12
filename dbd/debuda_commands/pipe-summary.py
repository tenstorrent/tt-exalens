import tt_util as util

command_metadata = {
    "long" : "pipe",
    "short" : "p",
    "type" : "high-level",
    "expected_argument_count" : 1,
    "arguments_description" : "pipe_id : prints details on the pipe with ID pipe_id"
}

def run (cmd, context, ui_state=None):
    pipe_id = int(cmd[1])

    graph_name = ui_state['current_graph_name']
    graph = context.netlist.graph(graph_name)
    pipe = graph.get_pipes(pipe_id).first()
    navigation_suggestions = [ ]
    if pipe:
        util.print_columnar_dicts ([pipe.root], [f"{util.CLR_INFO}Graph {graph_name}{util.CLR_END}"])

        for input_buffer in pipe.inputs():
            navigation_suggestions.append ({ 'cmd' : f"b {input_buffer}", 'description' : "Show src buffer" })
        for input_buffer in pipe.outputs():
            navigation_suggestions.append ({ 'cmd' : f"b {input_buffer}", 'description' : "Show dest buffer" })
    else:
        util.WARN (f"Cannot find pipe {pipe_id} in graph {graph_name}")

    return navigation_suggestions