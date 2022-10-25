"""
.. code-block::
   :caption: Example

        Current epoch:0(test_op) device:0 core:5-3 rc:2,4 stream:8 > p 10000300000
        Graph test_op
        --------------------  --------------------------------------------------------------------------------------------------------
        id                    10000300000 (0x2541077e0)
        input_list            [10000110000, 10000110008, 10000110016, 10000110024, 10000110004, 10000110012, 10000110020, 10000110028]
        pipe_periodic_repeat  0
        pipe_consumer_repeat  1
        output_list           [10000170000]
        incoming_noc_id       0
        outgoing_noc_id       0
        mcast_core_rc         [0, 0, 0]
"""
import tt_util as util

command_metadata = {
    "long" : "pipe",
    "short" : "p",
    "type" : "high-level",
    "expected_argument_count" : [ 1 ],
    "arguments" : "pipe_id",
    "description" : "Prints details on the pipe with ID 'pipe_id'."
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