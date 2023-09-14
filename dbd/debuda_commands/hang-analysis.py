"""
Usage:
  ha [ <verbose> ]

Arguments:
  verbose    Verbosity level (0 or 1) [default: 0]

Description:
  Traverses all devices looking for the point of failure in the netlist execution. The traversal is
  done in topological order with the intention of finding the first problematic core/stream.

Examples:
  ha
"""
import sys
from tabulate import tabulate
from tt_object import TTObjectIDDict
import tt_util as util
import tt_device
from tt_graph import Queue
from tt_coordinate import OnChipCoordinate
from docopt import docopt

def LOG(s, **kwargs):
    util.INFO (util.get_indent() + s, **kwargs)

command_metadata = {
    "short" : "ha",
    "type" : "high-level",
    "description" : __doc__
}

def queue_has_data(context, device_id, q:Queue):
    """
    Checking if queue has data
    """
    device = context.devices[device_id]
    if not q.is_host() and not q.is_dram():
        util.WARN(f'Unknown memory location: {q.get_loc()}')
        return True

    for mem_addr in q.get_mem_addr():
        if q.is_dram():
            dram_chan, dram_addr = mem_addr[0], mem_addr[1]
            x, y = device.DRAM_CHANNEL_TO_NOC0_LOC[dram_chan]
            read_ptr = device.pci_read_xy (x, y, 0, dram_addr)
            write_ptr = device.pci_read_xy (x, y, 0, dram_addr + 4)
        if q.is_host():
            host_chan, host_addr = mem_addr[0], mem_addr[1]
            read_ptr = tt_device.SERVER_IFC.host_dma_read (device_id, host_addr, host_chan)
            write_ptr = tt_device.SERVER_IFC.host_dma_read (device_id, host_addr+4, host_chan)

        # Get read and write pointers
        if Queue.occupancy(q.entries(), write_ptr, read_ptr) == 0:
            return False

    return True

# check if destination buffer is connected to source op
def is_destination_buffer(graph, src_op_or_q, dest_buffer):
    if graph.is_dest_buffer (dest_buffer):
        src_buffers = graph.get_fanin (dest_buffer)
        src_buffers.keep (lambda b: b.root["md_op_name"] == src_op_or_q.id())
        if src_buffers:
            return True
    return False

def is_stream_done(device, stream):
    moves_raw_data = stream.root["moves_raw_data"] if "moves_raw_data" in stream.root else False

    # LOG(f"Pretty print stream {stream}: {stream.pretty_print()}")

    stream_loc = OnChipCoordinate (*stream.loc(), "nocTr", device)

    if moves_raw_data:
        LOG (f"Stream '{stream}' moves raw data")
        REMOTE_DEST_BUF_SIZE = device.get_stream_reg_field(stream_loc, stream.stream_id(), 3, 0, 16)
        REMOTE_DEST_BUF_START = device.get_stream_reg_field(stream_loc, stream.stream_id(), 4, 0, 16)
        return REMOTE_DEST_BUF_SIZE == REMOTE_DEST_BUF_START
    else:
        return device.get_num_msgs_received(stream_loc, stream.stream_id()) == device.get_curr_phase_num_msgs_remaining(stream_loc, stream.stream_id())

def is_stream_active(device, stream):
    stream_loc = OnChipCoordinate (*stream.loc(), "nocTr", device)
    return device.get_stream_phase(stream_loc, stream.stream_id()) != 0 and device.get_num_msgs_received(stream_loc, stream.stream_id())  > 0

def is_stream_hung(device, stream):
    return not is_stream_done(device, stream) and not is_stream_active(device, stream)

def get_stream_data(device, stream):
    ret_type = dict()
    stream_loc = OnChipCoordinate (*stream.loc(), "nocTr", device)

    ret_type["phase"] = device.get_stream_phase(stream_loc, stream.stream_id())
    ret_type["msg_received"] = device.get_num_msgs_received(stream_loc, stream.stream_id())
    ret_type["msg_remaining"] = device.get_curr_phase_num_msgs_remaining(stream_loc, stream.stream_id())
    if device.get_remote_receiver(stream_loc, stream.stream_id()):
        ret_type["source"] = True
    if device.get_remote_source(stream_loc, stream.stream_id()):
        ret_type["dest"] = True
    return ret_type

def get_epoch_to_ops(context, device_id, epochs):
    epochs_ops_stream = {}
    device = context.devices[device_id]
    netlist = context.netlist
    epoch_id_graph = {}
    core_epoch_map = dict()  # Is this even used?
    for loc, epoch_id in epochs.items():
        xyloc = loc # (loc.to("noc0"))
        if xyloc not in core_epoch_map:
            core_epoch_map[xyloc] = epoch_id
        # get graph
        if epoch_id not in epoch_id_graph:
            graph_name = netlist.get_graph_name(epoch_id, device_id)
            if graph_name is None:
                continue
            epoch_id_graph[epoch_id] = {}
            epoch_id_graph[epoch_id]["graph_name"] = graph_name
            epoch_id_graph[epoch_id]["graph"] = netlist.graph(graph_name)

        graph_name = epoch_id_graph[epoch_id]["graph_name"]
        # get operation for loc
        op_name = epoch_id_graph[epoch_id]["graph"].location_to_op_name(loc)
        if epoch_id not in epochs_ops_stream:
            epochs_ops_stream[epoch_id] = dict()
        if op_name not in epochs_ops_stream[epoch_id]:
            epochs_ops_stream[epoch_id][op_name] = []

        epochs_ops_stream[epoch_id][op_name].append(loc)
    return epochs_ops_stream

# Returns if the Op wants more data on a given input
def get_streams_waiting_for_data (graph, device, src_op_or_q, dest_op_or_q):
    op_buffers = graph.get_buffers(dest_op_or_q)
    # As not all streams have buf_id, and not all have pipe_id, we try to find either one
    relevant_buffers = TTObjectIDDict()
    relevant_pipes = TTObjectIDDict()
    util.VERBOSE (f"Running wants_more_data_from_input for {dest_op_or_q} on input {src_op_or_q}")
    util.VERBOSE (f"  Found these buffers for {dest_op_or_q}: {op_buffers}")
    for dest_buffer_id, dest_buffer in op_buffers.items():
        if is_destination_buffer(graph, src_op_or_q, dest_buffer):
            relevant_buffers.add (dest_buffer)
            pipes = graph.get_pipes (dest_buffer)
            relevant_pipes.update (pipes)
    util.VERBOSE (f"  Found these source buffers for {src_op_or_q}->{dest_op_or_q} conection: {relevant_buffers}")
    relevant_streams = TTObjectIDDict({stream_id: stream for stream_id, stream in graph.streams.items() if relevant_buffers.find_id (stream.get_buffer_id()) or relevant_pipes.find_id(stream.get_pipe_id())})

    if not relevant_streams:
        buflist = [ str(buffer.id()) for buffer in relevant_buffers]
        util.WARN (f"No relevant streams for buffers {' '.join (buflist)}")
    else:
        util.VERBOSE (f"  Found these relevant_streams for {src_op_or_q}->{dest_op_or_q} conection: {' '.join ([ stream.__str__() for stream in relevant_streams ])}")

    streams_waiting_for_data = []
    for stream_id, stream in relevant_streams.items():
        if not is_stream_done(device, stream):
            streams_waiting_for_data.append(stream)
    return streams_waiting_for_data

def get_graph_input_queues(graph):
    input_queues = graph.queues().copy()
    # Keep only queues that are not fed by an op
    input_queues.keep (
        lambda q: q.root['input'] not in graph.ops
    )
    return input_queues

def get_input_queues_without_data(context, device_id, graph, verbose):
    """
    Finding input queues that do not have data
    """
    device = context.devices[device_id]
    input_queues = get_graph_input_queues(graph)
    queue_ops = {}
    for q_id, q in input_queues.items():
        has_data = queue_has_data(context, device_id, q)
        if not has_data:
            for op_id, op in graph.get_fanout(q).items():
                streams = get_streams_waiting_for_data (graph, device, q, op)
                if streams:
                    if q not in queue_ops: queue_ops[q] = {}
                    queue_ops[q][op] = []
                    for stream in streams:
                        data = get_stream_data(device, stream)
                        queue_ops[q][op].append([stream.on_chip_id(), "No data in queue", data])

    return queue_ops

def buffer_state (context, graph, device_id, buffer):
    device = context.devices[device_id]
    buffer_streams = graph.get_streams (buffer)

    processed_tiles = None
    for stream_id, stream in buffer_streams.items():
        stream_loc = OnChipCoordinate (*stream.loc(), "nocTr", device)
        processed_tiles = device.get_num_msgs_received(stream_loc, stream.stream_id())

    ret_val = { "epoch_tiles": buffer.root["epoch_tiles"], "processed_tiles": processed_tiles, "epoch_tiles": buffer.root["epoch_tiles"] }
    return ret_val

def detect_and_report_pipe_hang (context, graph, device_id, pipe):
    device = context.devices[device_id]

    """
    Analyzing pipe for hangs
    """
    in_buffers = graph.get_buffers (pipe, "in")
    in_streams = graph.get_streams (in_buffers)

    for buffer_id, buffer in in_buffers.items():
        bs = buffer_state (context, graph, device_id, buffer)

    out_buffers = graph.get_buffers (pipe, "out")
    out_streams = graph.get_streams (out_buffers)

    pipe_streams = graph.get_streams (pipe)
    LOG (f"Pipe streams (for all phases): {pipe_streams}")

    phases = dict()
    for ps_id, ps in pipe_streams.items():
        phases_key = ( OnChipCoordinate (*ps.loc(), "nocTr", device), ps.stream_id() )
#        if phases_key not in phases:
        phases[phases_key] = device.get_stream_phase (*phases_key)
    phase_values = set (phases.values())
    pipe_streams.keep (lambda ps: ps.phase_id() in phase_values)
    LOG (f"pipe_streams in phase: {pipe_streams}")

    for ps_id, ps in pipe_streams.items():
        is_src = ps.is_src()
        if is_src:
            in_streams.add (ps)
        else:
            out_streams.add (ps)

    LOG (f"in_buffers: {in_buffers}, in_streams: {in_streams}")
    LOG (f"out_buffers: {out_buffers}, out_streams: {out_streams}")

    LOG (f"Summary:")
    hang_details = None
    for in_stream_id, in_stream in in_streams.items():
        stream_hung = is_stream_hung(device, in_stream)
        hang_details = hang_details or stream_hung
        LOG (f"  Input stream {in_stream} -> Active: {is_stream_active(device, in_stream)}, Done: {is_stream_done(device, in_stream)} Hung: {stream_hung}")

    for out_stream_id, out_stream in out_streams.items():
        stream_hung = is_stream_hung(device, out_stream)
        hang_details = hang_details or stream_hung
        LOG (f"  Output stream {out_stream} -> Active: {is_stream_active(device, out_stream)}, Done: {is_stream_done(device, out_stream)} Hung: {stream_hung}")
    return hang_details

def get_buffer_state (context, graph, device_id, stream, buffer):
    device = context.devices[device_id]
    stream_loc = OnChipCoordinate (*stream.loc(), "nocTr", device)

    # Get num_messages_received for the stream
    num_messages_received = device.get_num_msgs_received(stream_loc, stream.stream_id())
    # Get tile_clear_granularity from buffer
    tile_clear_granularity = buffer.root["tile_clear_granularity"]

    buffer_ready = num_messages_received > 0 and num_messages_received % tile_clear_granularity == 0
    return buffer_ready

def is_op_hung (context, graph, device_id, op):
    LOG (f"Checking op {op}")
    device = context.devices[device_id]

    # Find all input buffers for the op
    input_buffers = graph.get_buffers (op, "out")

    # LOG(f"Input buffers for {op}: {input_buffers}")

    buffer_state = dict()
    for buffer_id, buffer in input_buffers.items():
        if buffer.is_input_of_pipe() and buffer.is_output_of_pipe():
            # util.WARN (f"Ignoring buffer {buffer} as it is both input and output of a pipe")
            continue

        # Get all stream for the buffer
        for s_id, stream in graph.streams.items():
            if stream.get_buffer_id() == buffer_id:
                stream_loc = OnChipCoordinate (*stream.loc(), "nocTr", device)
                phase = device.get_stream_phase(stream_loc, stream.stream_id())
                if phase == stream.phase_id():
                    buffer_state[buffer_id] = get_buffer_state (context, graph, device_id, stream, buffer)
                    # LOG (f"Buffer {buffer} is ready: {buffer_state[buffer_id]}")

    # If there is a mix of ready/non-ready report a warning
    if True in buffer_state.values() and False in buffer_state.values():
        ready_ops = set()
        non_ready_ops = set()
        util.WARN (f"Mix of ready/non-ready buffers for op {op}")
        for buffer_id, buffer_ready in buffer_state.items():
            buffer = graph.buffers[buffer_id]
            src_buffers = graph.get_buffers (buffer.output_of_pipes, "in")
            src_ops = { src_buffers[src_buffer_id].root["md_op_name"] for src_buffer_id in src_buffers }
            if buffer_ready:
                ready_ops.update (src_ops)
            else:
                non_ready_ops.update (src_ops)
        util.WARN (f"  Ready operations:     {', '.join(list(ready_ops))}")
        util.WARN (f"  Non-ready operations: {', '.join(list(non_ready_ops))}")

# go through all operation in topological
# order and search for the first stream
# that is not done and not active
def find_ops_with_hang(context, graph, device_id, verbose):
    """
    Looking for hangs in a graph
    """
    found_hangs=dict()
    for op_id, op in graph.ops.items():
        op_status = is_op_hung (context, graph, device_id, op)
        if op_status:
            found_hangs[op_id] = op_status

        # Early exit if we found a hang
        if found_hangs and not verbose:
            return found_hangs
    return found_hangs

def print_hung_ops(ops_with_hang_list):
    column_format = [
            { 'key_name' : 'device',      'title': 'Device ID',                 'formatter' : None},
            { 'key_name' : 'epoch',       'title': 'Epoch ID',                  'formatter' : None},
            { 'key_name' : 'graph',       'title': 'Graph Name',                'formatter' : None},
            { 'key_name' : 'src',         'title': 'Source',                    'formatter' : None},
            { 'key_name' : 'dst',         'title': 'Destination',               'formatter' : None},
            { 'key_name' : 'hang',        'title': 'Hang Reason',               'formatter' : lambda x: f"{util.CLR_RED}{x}{util.CLR_END}"},
            { 'key_name' : 'stream',      'title': 'Stream',                    'formatter' : None},
            { 'key_name' : 'info',        'title': 'Additional Stream Info',    'formatter' : None},
        ]
    table=util.TabulateTable(column_format)
    table.rows = [ ]
    only_show_first_row = True
    multiple_streams_per_link_collapsed = False
    for element in ops_with_hang_list:
        for src, dst_streams in element['operations'].items():
            for dst, details in dst_streams.items():
                row = { 'device': element['device_id'], 'epoch':element['epoch_id'], 'graph': element['graph_name'], 'src' : src, 'dst' : dst}
                first_row_for_link = True
                for stream_details in details:
                    stream_coords, hang_message, additional_info = stream_details
                    row.update({'hang' : hang_message, 'stream' : stream_coords, 'info' : additional_info})
                    if only_show_first_row:
                        if len(details) > 1:
                            more_streams_str = f'... {len(details)-1} more'
                            if row['stream'] is None:
                                row['stream'] = (more_streams_str,)
                            elif type(row['stream']) is tuple:
                                row['stream'] += (more_streams_str,)
                            else:
                                util.WARN (f"Unhandled type for row['stream']: {type(row['stream'])}")

                            table.add_row(None, row)
                            multiple_streams_per_link_collapsed = False
                            break
                    if first_row_for_link:
                        table.add_row(None, row)
                    row = { 'device': '', 'epoch': '', 'graph': '', 'src' : '', 'dst' : ''}
                    first_row_for_link = False

    if table.rows:
        print (table)
        if multiple_streams_per_link_collapsed:
            print (f"Note: Some src->dest links contain multiple hung streams, only the first one is shown.")

def get_navigation_suggestion_for_hanged_ops(ops_with_hang_list):
    navigation_suggestions = []
    return navigation_suggestions

    for element in ops_with_hang_list:
        for src, dst_streams in element['operations'].items():
            for dst, streams in dst_streams.items():
                for stream_with_desc in streams:
                    # FIX: This does not know about the device, so it will not work for multi-device.
                    navigation_suggestions.append ({ 'cmd' : f"s {stream_with_desc[0][0]} {stream_with_desc[0][1]} {stream_with_desc[0][2]}", 'description' : f"Go to stream {stream_with_desc[0]}" })
    return navigation_suggestions

def read_device_epochs(device):
    """
    Read all cores on a device and return a dictionary of epoch_id to core locations
    :return: { epoch_id : [ core_loc ] }
    """
    cte = device.read_core_to_epoch_mapping()
    epoch_to_core_locs = dict()
    for loc, epoch_id in cte.items():
        if epoch_id not in epoch_to_core_locs:
            epoch_to_core_locs[epoch_id] = set()
        epoch_to_core_locs[epoch_id].add(loc)

    return epoch_to_core_locs

def read_current_epochs(context):
    """
    Probing all devices for all active cores and their current epochs
    :return: { device_id : { epoch_id : [ core_loc ] } }
    """
    device_id_to_epoch_dict = dict()

    for device_id, _ in context.netlist.device_graph_names().items():
        device = context.devices[device_id]
        device_id_to_epoch_dict[device_id] = read_device_epochs(device)
    return device_id_to_epoch_dict

def run(cmd_text, context, ui_state = None):
    args = docopt(__doc__, argv=cmd_text.split()[1:])
    verbose = 0 if args['<verbose>'] is None else int(args['<verbose>'])
    util.INFO(f"Running hang analysis (verbose={verbose})")

    navigation_suggestions = []
    queue_ops_missing_data = []
    ops_with_hang_list = []

    # A. Run analysis on all devices
    device_id_to_epoch_dict = read_current_epochs(context)
    for device_id in device_id_to_epoch_dict:
        epoch_id_list = list(device_id_to_epoch_dict[device_id].keys())
        epoch_id_list.sort()
        if len(epoch_id_list) > 1:
            # FINISH: This scenario has not been tested
            util.WARN (f"More than one epoch running on device {device_id}):")
        LOG (f"Epochs running on device {device_id}: {util.space_join(epoch_id_list)}")

        for epoch_id in epoch_id_list:
            graph_name = context.netlist.get_graph_name(epoch_id, device_id)
            if graph_name is None:
                LOG (f"- Skipping epoch {epoch_id}, as there is no information on epoch {epoch_id} in the netlist")
                continue
            LOG (f"Analyzing graph {graph_name} ( epoch {epoch_id} )")
            graph = context.netlist.graph(graph_name)

            # -- 1. Check input queues
            # WIP - bring this back in
            # queue_ops_errors = get_input_queues_without_data(context, device_id, graph, verbose)
            # if len(queue_ops_errors) > 0:
            #     queue_ops_missing_data.append({'device_id':device_id, 'epoch_id':epoch_id, 'graph_name':graph_name, 'operations':queue_ops_errors})
            #     util.ERROR(f"Found {len(queue_ops_errors)} input queues without data: {list (queue_ops_errors.keys())}")

            # -- 2. Check hung ops
            ops_with_hang = find_ops_with_hang(context, graph, device_id, verbose)
            if ops_with_hang:
                ops_with_hang_list.append({'device_id':device_id, 'epoch_id':epoch_id, 'graph_name':graph_name, 'operations':ops_with_hang})

    # B. Report results
    all_good = True
    if queue_ops_missing_data:
        all_good = False
        navigation_suggestions.extend(get_navigation_suggestion_for_hanged_ops(queue_ops_missing_data))
        util.ERROR ("The following queues do not have data:")
        print_hung_ops(queue_ops_missing_data)
    if ops_with_hang_list:
        all_good = False
        util.ERROR ("The following operations are hung:")
        print_hung_ops(ops_with_hang_list)
        navigation_suggestions.extend(get_navigation_suggestion_for_hanged_ops(ops_with_hang_list))

    if all_good:
        util.INFO ("No issues detected")
    return navigation_suggestions

# Turn on tracing for function calls in this module. This prints docstrings and and arguments.
# util.decorate_all_module_functions_for_tracing(sys.modules[__name__], LOG)