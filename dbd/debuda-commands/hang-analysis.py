from tabulate import tabulate
from dbd.tt_object import TTObjectSet
import tt_util as util
from tt_graph import Queue, Op
import tt_device

command_metadata = {
        "short" : "ha",
        "expected_argument_count" : 0,
        "arguments_description" : ": Prints operation summary"
    }

# checks wheter queue has data
def queue_has_data(device, q:Queue):
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
            read_ptr = tt_device.PCI_IFC.host_dma_read (mem_addr)
            write_ptr = tt_device.PCI_IFC.host_dma_read (mem_addr+4)

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

# some stream helper functions
# TODO: This should be part of stream
def is_stream_done(device, stream):
    return device.get_num_msgs_received(stream.noc0_XY(), stream.stream_id()) == device.get_curr_phase_num_msgs_remaining(stream.noc0_XY(), stream.stream_id())

def is_stream_active(device, stream):
    return device.get_stream_phase(stream.noc0_XY(), stream.stream_id()) != 0 and device.get_num_msgs_received(stream.noc0_XY(), stream.stream_id())  > 0

def is_stream_hang(device, stream):
    return not is_stream_done(device, stream) and not is_stream_active(device, stream)

def get_stream_data(device, stream):
    ret_type = dict()
    ret_type["phase"] = device.get_stream_phase(stream.noc0_XY(), stream.stream_id())
    ret_type["msg_received"] = device.get_num_msgs_received(stream.noc0_XY(), stream.stream_id())
    ret_type["msg_reamining"] = device.get_curr_phase_num_msgs_remaining(stream.noc0_XY(), stream.stream_id())
    if device.get_remote_receiver(stream.noc0_XY(), stream.stream_id()):
        ret_type["source"] = True
    if device.get_remote_source(stream.noc0_XY(), stream.stream_id()):
        ret_type["dest"] = True
    return ret_type

def get_epoch_to_ops(context, device_id, epochs):
    epochs_ops_stream = {}
    device = context.devices[device_id]
    netlist = context.netlist
    epoch_id_graph = {}
    for loc, epoch_id in epochs.items():
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
        row, col = device.noc0_to_rc((loc[0], loc[1]))
        op_name = epoch_id_graph[epoch_id]["graph"].core_coord_to_op_name((row,col))
        if epoch_id not in epochs_ops_stream:
            epochs_ops_stream[epoch_id] = dict()
        if op_name not in epochs_ops_stream[epoch_id]:
            epochs_ops_stream[epoch_id][op_name] = []

        epochs_ops_stream[epoch_id][op_name].append(loc)
    return epochs_ops_stream

# Returns if the Op wants more data on a given input
def get_streams_waiting_for_data (graph, device, src_op_or_q, dest_op_or_q):
    op_buffers = graph.get_buffers(dest_op_or_q)
    # As not all streams have buf_id, and not all have pipe_id, we try to find either
    relevant_buffers = TTObjectSet()
    relevant_pipes = TTObjectSet()
    util.VERBOSE (f"Running wants_more_data_from_input for {dest_op_or_q} on input {src_op_or_q}")
    util.VERBOSE (f"  Found these buffers for {dest_op_or_q}: {op_buffers}")
    for dest_buffer in op_buffers:
        if is_destination_buffer(graph, src_op_or_q, dest_buffer):
            relevant_buffers.add (dest_buffer)
            pipes = graph.get_pipes (dest_buffer)
            relevant_pipes.update (pipes)
    util.VERBOSE (f"  Found these source buffers for {src_op_or_q}->{dest_op_or_q} conection: {relevant_buffers}")
    relevant_streams = util.set({stream for stream in graph.streams if relevant_buffers.find_id (stream.get_buffer_id()) or relevant_pipes.find_id(stream.get_pipe_id())})

    if not relevant_streams:
        buflist = [ str(buffer.id()) for buffer in relevant_buffers]
        util.WARN (f"No relevant streams for buffers {' '.join (buflist)}")
    else:
        util.VERBOSE (f"  Found these relevant_streams for {src_op_or_q}->{dest_op_or_q} conection: {' '.join ([ stream.__str__() for stream in relevant_streams ])}")

    streams_waiting_for_data = []
    for stream in relevant_streams:
        if not is_stream_done(device, stream):
            streams_waiting_for_data.append(stream)
    return streams_waiting_for_data

def get_graph_input_queues(graph):
    input_queues = graph.get_fanin(graph.ops)
    input_queues.keep (lambda q: q.root['type'] == 'queue')
    return input_queues

def get_input_queues_without_data(device, graph):
    input_queues = get_graph_input_queues(graph)
    queue_ops = {}
    for q in input_queues:
        has_data = queue_has_data(device, q)
        if not has_data:
            for op in graph.get_fanout(q):
                streams = get_streams_waiting_for_data (graph, device, q, op)
                if streams:
                    if q not in queue_ops: queue_ops[q] = {}
                    queue_ops[q][op] = []
                    for stream in streams:
                        data = get_stream_data(device, stream)
                        queue_ops[q][op].append([stream.on_chip_id(), "No data in queue", data])

    return queue_ops

# go through all operation in topological
# order and searchs for first stream
# that is not done and not active
def find_ops_with_hang(graph, device):
    input_queues = get_graph_input_queues(graph)
    ops_to_visit = graph.get_fanout(input_queues)
    visited_ops = set ()
    ops_pipes = graph.get_ops_pipes()
    # dictionary with stream location and 
    found_hangs = {}
    while ops_to_visit:
        # initialize list of fanout ops
        new_ops_to_visit = TTObjectSet()
        for src_op in ops_to_visit:
            assert(src_op not in visited_ops)
            src_pipes = ops_pipes[src_op.id()]
            dest_ops = graph.get_fanout (src_op)
            for dest_op in dest_ops:
                if dest_op.id() not in ops_pipes:
                    # currently we are not handling op to queue
                    continue
                dest_pipes = ops_pipes[dest_op.id()]
                new_ops_to_visit.add(dest_op)

                connecting_pipes = src_pipes.intersection (dest_pipes)

                pipe_streams = graph.get_streams (connecting_pipes)

                pipe_streams.update (graph.get_streams (graph.get_buffers (connecting_pipes)))

                assert pipe_streams, "No streams found for connection {src_op}->{dest_op}"

                for stream in pipe_streams:
                    if is_stream_hang(device, stream):
                        if src_op not in found_hangs: found_hangs[src_op] = {}
                        if dest_op not in found_hangs[src_op]: found_hangs[src_op][dest_op] = []
                        data = get_stream_data(device, stream)
                        found_hangs [src_op][dest_op].append([stream.on_chip_id(), "Data not received", data])

        if found_hangs:
            return found_hangs

        visited_ops.update(ops_to_visit)

        # add new ops to visit
        ops_to_visit = TTObjectSet()
        for new_op in new_ops_to_visit:
            fan_in_ops = graph.get_fanin(new_op)
            if fan_in_ops.issubset(visited_ops):
                ops_to_visit.add(new_op)
    return None

def print_hanged_ops(ops_with_hang_list):
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
    for element in ops_with_hang_list:
        for src, dst_streams in element['operations'].items():
            for dst, details in dst_streams.items():
                row = { 'device': element['device_id'], 'epoch':element['epoch_id'], 'graph': element['graph_name'], 'src' : src, 'dst' : dst}
                for stream_details in details:
                    stream_coords, hang_message, additional_info = stream_details
                    row.update({'hang' : hang_message, 'stream' : stream_coords, 'info' : additional_info})
                    table.add_row(None, row)
                    row = { 'device': '', 'epoch': '', 'graph': '', 'src' : '', 'dst' : ''}

    if table.rows:
        print (table)

def get_navigation_suggestion_for_hanged_ops(ops_with_hang_list):
    navigation_suggestions = []
    for element in ops_with_hang_list:
        for src, dst_streams in element['operations'].items():
            for dst, streams in dst_streams.items():
                for stream_with_desc in streams:
                    navigation_suggestions.append ({ 'cmd' : f"s {stream_with_desc[0][0]} {stream_with_desc[0][1]} {stream_with_desc[0][2]}", 'description' : f"Go to stream {stream_with_desc[0]}" })
    return navigation_suggestions

def run(args, context, ui_state = None):
    navigation_suggestions = []
    queue_ops_missing_data = []
    ops_with_hang_list = []

    for device_id, graph_names in context.netlist.device_graph_names().items():
        util.INFO(f"Analyzing device {device_id}")
        device = context.devices[device_id]
        util.INFO (f"  Reading epochs for locations")
        epochs = device.read_all_epochs()
        epoch_ops_streams = get_epoch_to_ops(context, device_id, epochs)
        if len(epoch_ops_streams.keys()) > 1:
            # This has not been tested
            util.WARN (f"  More than one epoch running on device (epochs: {list(epoch_ops_streams.keys())})")

        # handle graph that is running on device
        for epoch_id, ops_streams in epoch_ops_streams.items():
            graph_name = graph_names[epoch_id]
            util.INFO (f"    Analyzing graph {graph_name} ( epoch {epoch_id} )")
            graph = context.netlist.graph(graph_name)

            # check input queues
            queue_ops_errors = get_input_queues_without_data(device, graph)

            if len(queue_ops_errors) > 0:
                queue_ops_missing_data.append({'device_id':device_id, 'epoch_id':epoch_id, 'graph_name':graph_name, 'operations':queue_ops_errors})
                continue

            # check hanged operations
            ops_with_hang = find_ops_with_hang(graph, device)
            if ops_with_hang:
                ops_with_hang_list.append({'device_id':device_id, 'epoch_id':epoch_id, 'graph_name':graph_name, 'operations':ops_with_hang})

    print_hanged_ops(queue_ops_missing_data)
    print_hanged_ops(ops_with_hang_list)

    navigation_suggestions = get_navigation_suggestion_for_hanged_ops(queue_ops_missing_data)
    navigation_suggestions.extend(get_navigation_suggestion_for_hanged_ops(ops_with_hang_list))

    return navigation_suggestions