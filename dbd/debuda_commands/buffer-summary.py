"""
.. code-block::
   :caption: Example

        Current epoch:0(test_op) device:0 core:5-3 rc:2,4 stream:8 > b 10000170000
        Graph test_op
        ----------------------------  -------------------------
        md_op_name                    matmul2
        id                            0
        uniqid                        10000170000 (0x2540e7c10)
        epoch_tiles                   32 (0x20)
        chip_id                       [0]
        core_coordinates              (2, 4)
        size_tiles                    32 (0x20)
        scatter_gather_num_tiles      16 (0x10)
        ...
"""
import tt_util as util

command_metadata = {
    "long" : "buffer",
    "short" : "b",
    "type" : "low-level",
    "expected_argument_count" : [ 1 ],
    "arguments" : "buffer_id",
    "description" : "Prints details on the buffer with a given ID."
}

# Find occurrences of buffer with ID 'buffer_id' across all epochs, and print the structures that reference them
def run (cmd, context, ui_state=None):
    try:
        buffer_id = int(cmd[1])
    except ValueError as e:
        buffer_id = cmd[1]

    navigation_suggestions = [ ]

    graph_name = ui_state['current_graph_name']
    graph = context.netlist.graph(graph_name)

    if type(buffer_id) == int:
        buffer = graph.get_buffers(buffer_id).first()
        if not buffer:
            util.WARN(f"Cannot find buffer {buffer_id} in graph {graph_name}")
        else:
            util.print_columnar_dicts ([buffer.root], [f"{util.CLR_INFO}Graph {graph_name}{util.CLR_END}"])

            for pipe_id, pipe in graph.pipes.items():
                if buffer_id in pipe.root["input_list"]:
                    print (f"( {util.CLR_BLUE}Input{util.CLR_END} of pipe {pipe.id()} )")
                    navigation_suggestions.append ({ 'cmd' : f"p {pipe.id()}", 'description' : "Show pipe" })
                if buffer_id in pipe.root["output_list"]:
                    print (f"( {util.CLR_BLUE}Output{util.CLR_END} of pipe {pipe.id()} )")
                    navigation_suggestions.append ({ 'cmd' : f"p {pipe.id()}", 'description' : "Show pipe" })
    else:
        util.WARN (f"Buffer ID must be an integer")

    return navigation_suggestions
