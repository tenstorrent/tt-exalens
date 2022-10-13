"""Documentation for graph
"""
command_metadata = {
    "short" : "g",
    "type" : "high-level",
    "expected_argument_count" : [ 1 ],
    "arguments" : "graph_name",
    "description" : "Changes the current active graph."
}

import tt_util as util

def run(args, context, ui_state = None):
    """Run command
    """
    navigation_suggestions = []

    gname = args[1]
    if gname not in context.netlist.graph_names():
        util.WARN (f"Invalid graph {gname}. Available graphs: {', '.join (list(context.netlist.graph_names()))}")
    else:
        ui_state["current_graph_name"] = args[1]

    return navigation_suggestions
