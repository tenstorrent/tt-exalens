command_metadata = {
    "short" : "s",
    "expected_argument_count" : 3,
    "arguments_description" : "x y stream_id : show stream 'stream_id' at core 'x-y'"
}

import tt_stream, tt_util as util

# Prints all information on a stream
def run(args, context, ui_state = None):
    x, y, stream_id = int(args[1]), int(args[2]), int(args[3])
    current_device_id = ui_state["current_device_id"]
    current_device = context.devices[current_device_id]

    regs = current_device.read_stream_regs ((x, y), stream_id)
    stream_regs = tt_stream.convert_reg_dict_to_strings(current_device, regs)
    stream_epoch_id = regs["CURR_PHASE"] >> 10
    new_current_epoch_id = stream_epoch_id

    all_stream_summary, navigation_suggestions = tt_stream.get_core_stream_summary (current_device, x, y)
    data_columns = [ all_stream_summary ] if len(all_stream_summary) > 0 else []
    title_columns = [ f"{util.CLR_WARN}Non-idle streams{util.CLR_END}" ] if len(all_stream_summary) > 0 else []

    data_columns.append (stream_regs)
    title_columns.append ("Registers")

    # 1. Append blobs
    buffer_ids = set()
    non_active_phases = dict()
    graph = context.netlist.graphs[context.netlist.epoch_id_to_graph_name(stream_epoch_id)]

    # 2. Find blob data
    stream_loc = (current_device_id, x, y, stream_id, int(regs['CURR_PHASE']))
    if stream_loc in graph.streams:
        stream_from_blob = graph.streams[stream_loc].root
        buf_id = stream_from_blob["buf_id"] if stream_from_blob and "buf_id" in stream_from_blob else None
        if buf_id is not None:
            buffer_ids.add (buf_id)
        data_columns.append (stream_from_blob)
        title_columns.append ("Stream (blob.yaml)")

    # 2. Append buffers
    for buffer_id in buffer_ids:
        data_columns.append (graph.buffers[buffer_id].root)
        title_columns.append (f"Buffer {buffer_id}")

    # 3. Append relevant pipes
    for buffer_id in buffer_ids:
        pipe_ids = graph.get_pipes_for_buffer(buffer_id)
        for pipe_id in pipe_ids:
            pipe = graph.get_pipe (pipe_id)
            title_columns.append (f"Pipe {pipe_id}")
            data_columns.append (pipe.root)

    util.print_columnar_dicts (data_columns, title_columns)

    if new_current_epoch_id != stream_epoch_id:
        print (f"{util.CLR_WARN}Current epoch is {new_current_epoch_id}, while the stream is in epoch {stream_epoch_id} {util.CLR_END}. To switch to epoch {stream_epoch_id}, enter {util.CLR_PROMPT}e {stream_epoch_id}{util.CLR_END}")

    # 4. TODO: Print forks

    return navigation_suggestions