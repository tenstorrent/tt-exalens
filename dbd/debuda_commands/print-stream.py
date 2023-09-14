"""
Usage:
  stream <x> <y> <stream-id>

Arguments:
  x          nocTr X coordinate of the core
  y          nocTr Y coordinate of the core
  stream-id  Stream ID

Description:
  Shows stream 'stream_id' at core 'x-y' on the current device.

Examples:
  s 1 1 4
"""

command_metadata = {
    "short" : "s",
    "type" : "low-level",
    "description" : __doc__
}

import tt_stream, tt_util as util
from tt_coordinate import OnChipCoordinate
from docopt import docopt

# Prints all information on a stream
def run(cmd_text, context, ui_state = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])
    current_device_id = ui_state["current_device_id"]
    current_device = context.devices[current_device_id]

    x = int(args['<x>'], 0)
    y = int(args['<y>'], 0)
    stream_id = int(args['<stream-id>'], 0)

    stream_loc = OnChipCoordinate(x, y, "nocTr", device=current_device)
    regs = current_device.read_stream_regs (stream_loc, stream_id)
    stream_regs = tt_stream.convert_reg_dict_to_strings(current_device, regs)
    stream_epoch_id = current_device.get_epoch_id(stream_loc)
    new_current_epoch_id = stream_epoch_id

    all_stream_summary, navigation_suggestions = tt_stream.get_core_stream_summary (current_device, stream_loc)

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
        try:
            op_name = graph.location_to_full_op_name (loc)
            n['description'] += f" ({op_name})"
        except:
            n['description'] += " N/A"

    # 2. Find blob data
    stream_id_tuple = (current_device_id, *stream_loc.to('nocTr'), stream_id, int(regs['CURR_PHASE']))
    stream_set = graph.get_streams(stream_id_tuple)

    if len(stream_set) == 1:
        stream_from_blob = stream_set.first().root
        data_columns.append (stream_from_blob)
        title_columns.append ("Stream (blob.yaml)")
        # If there is an associated buffer, add it for showing.
        buf_id = stream_from_blob.get ("buf_id", None)
        if buf_id is not None:
            buffer_ids.add (buf_id)
    elif len(stream_set) == 0:
        util.WARN (f"Cannot find stream {stream_id_tuple} in blob data of graph {graph.id()}")
    else:
        util.WARN (f"Multiple streams found at {stream_id_tuple} in blob data of graph {graph.id()}")

    # 2. Append buffers
    buffers = graph.get_buffers (buffer_ids)
    for b_id, b in buffers.items():
        title_columns.append (f"Buffer {b.id()}")
        data_columns.append (b.root)

    # 3. Append relevant pipes
    pipes = graph.get_pipes(buffers)
    for pipe_id, pipe in pipes.items():
        title_columns.append (f"Pipe {pipe.id()}")
        data_columns.append (pipe.root)

    util.print_columnar_dicts (data_columns, title_columns)

    if new_current_epoch_id != stream_epoch_id:
        print (f"{util.CLR_WARN}Current epoch is {new_current_epoch_id}, while the stream is in epoch {stream_epoch_id} {util.CLR_END}. To switch to epoch {stream_epoch_id}, enter {util.CLR_PROMPT}e {stream_epoch_id}{util.CLR_END}")
    else:
        print(f"Stream epoch is {stream_epoch_id}")

    # 4. TODO: Print forks

    # Update the current UI state
    ui_state["current_loc"] = stream_loc
    ui_state["current_stream_id"] = stream_id
    return navigation_suggestions