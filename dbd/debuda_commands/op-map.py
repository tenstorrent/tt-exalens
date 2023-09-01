"""
.. code-block::
   :caption: Example

        Current epoch:0(test_op) device:0 core:1-1 rc:0,0 stream:8 > op-map
        Graph/Op         Op type       Epoch    Device  Netlist Loc    NOC0 Loc    Grid Size
        ---------------  ----------  -------  --------  ----------  ----------  -----------
        test_op/add1     add               0         0  [2, 6]      7-3         [1, 1]
        test_op/d_op3    datacopy          0         0  [0, 3]      4-1         [1, 1]
        test_op/f_op0    datacopy          0         0  [0, 0]      1-1         [1, 1]
        test_op/f_op1    datacopy          0         0  [0, 1]      2-1         [1, 1]
        test_op/matmul1  matmul            0         0  [0, 2]      3-1         [1, 1]
        test_op/matmul2  matmul            0         0  [2, 4]      5-3         [1, 1]
        test_op/recip    reciprocal        0         0  [2, 2]      3-3         [1, 1]
"""

from tabulate import tabulate
from tt_coordinate import OnChipCoordinate

command_metadata = {
    "short" : "om",
    "type" : "high-level",
    "expected_argument_count" : [ 0 ],    "arguments" : "",
    "description" : "Draws a mini map of the current epoch."
}

def run(args, context, ui_state = None):
    navigation_suggestions = []

    rows = []
    for graph_id, graph in context.netlist.graphs.items():
        graph_name = graph.id()
        epoch_id = context.netlist.graph_name_to_epoch_id (graph_name)
        device_id = context.netlist.graph_name_to_device_id (graph_name)
        device = context.devices[device_id]
        for op_name in graph.op_names():
            op = graph.root[op_name]
            loc = OnChipCoordinate (*op['grid_loc'], "netlist", device)
            row = [ f"{graph_name}/{op_name}", op['type'], epoch_id, f"{graph.root['target_device']}", f"{loc.to_str('netlist')}", f"{loc.to_str('nocTr')}", f"{op['grid_size']}"]
            rows.append (row)

    print (tabulate(rows, headers = [ "Graph/Op", "Op type", "Epoch", "Device", "Netlist Loc", "NOC Tr", "Grid Size" ]))

    return navigation_suggestions