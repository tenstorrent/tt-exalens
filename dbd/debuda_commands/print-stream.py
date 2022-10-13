command_metadata = {
    "short" : "s",
    "long" : "stream",
    "type" : "low-level",
    "expected_argument_count" : [ 3 ],
    "arguments" : "x y stream_id",
    "description" : "Shows stream 'stream_id' at core 'x-y'"
}

import tt_stream, tt_util as util

# Prints all information on a stream
def run(args, context, ui_state = None):
    noc0_loc, stream_id = (int(args[1]), int(args[2])), int(args[3])
    current_device_id = ui_state["current_device_id"]
    current_device = context.devices[current_device_id]

    regs = current_device.read_stream_regs ((noc0_loc), stream_id)
    stream_regs = tt_stream.convert_reg_dict_to_strings(current_device, regs)
    stream_epoch_id = regs["CURR_PHASE"] >> 10
    new_current_epoch_id = stream_epoch_id

    all_stream_summary, navigation_suggestions = tt_stream.get_core_stream_summary (current_device, noc0_loc)

    # Initialize with the summary of all streams within the core (if any)
    data_columns = [ all_stream_summary ] if len(all_stream_summary) > 0 else []
    title_columns = [ f"Non-idle streams" ] if len(all_stream_summary) > 0 else []

    data_columns.append (stream_regs)
    title_columns.append ("Registers")

    # 1. Append blobs
    buffer_ids = util.set()
    non_active_phases = dict()
    graph = context.netlist.graph(ui_state["current_graph_name"])

    # 1a. Append the op name to description
    for n in navigation_suggestions:
        loc = n['loc']
        loc_rc = current_device.noc0_to_rc(loc)
        op_name = graph.core_coord_to_full_op_name (loc_rc)
        n['description'] += f" ({op_name})"

    # 2. Find blob data
    stream_loc = (current_device_id, *noc0_loc, stream_id, int(regs['CURR_PHASE']))
    stream_set = graph.get_streams(stream_loc)

    if len(stream_set) == 1:
        stream_from_blob = stream_set.first().root
        data_columns.append (stream_from_blob)
        title_columns.append ("Stream (blob.yaml)")
        # If there is an associated buffer, add it for showing.
        buf_id = stream_from_blob.get ("buf_id", None)
        if buf_id is not None:
            buffer_ids.add (buf_id)
    elif len(stream_set) == 0:
        util.WARN (f"Cannot find stream {stream_loc} in blob data of graph {graph.id()}")
    else:
        util.WARN (f"Multiple streams found at {stream_loc} in blob data of graph {graph.id()}")

    # 2. Append buffers
    buffers = graph.get_buffers (buffer_ids)
    for b in buffers:
        title_columns.append (f"Buffer {b.id()}")
        data_columns.append (b.root)

    # 3. Append relevant pipes
    pipes = graph.get_pipes(buffers)
    for pipe in pipes:
        title_columns.append (f"Pipe {pipe.id()}")
        data_columns.append (pipe.root)

    util.print_columnar_dicts (data_columns, title_columns)

    if new_current_epoch_id != stream_epoch_id:
        print (f"{util.CLR_WARN}Current epoch is {new_current_epoch_id}, while the stream is in epoch {stream_epoch_id} {util.CLR_END}. To switch to epoch {stream_epoch_id}, enter {util.CLR_PROMPT}e {stream_epoch_id}{util.CLR_END}")

    # 4. TODO: Print forks

    # Update the current UI state
    ui_state["current_x"] = noc0_loc[0]
    ui_state["current_y"] = noc0_loc[1]
    ui_state["current_stream_id"] = stream_id
    return navigation_suggestions