"""Traverses all streams and detects the blocked one. It then prints the results.
It prioritizes the streams that are genuinely blocked, to the ones that are waiting on genuinely
blocked cores.
"""
from tabulate import tabulate
import tt_util as util
import tt_netlist

command_metadata = {
    "short" : "t",
    "type" : "high-level",
    "expected_argument_count" : 2,
    "arguments" : "tile_id, raw",
    "description" : "Prints tile for the current stream in the currently active phase. If raw=1, prints raw bytes."
}

# converts data format to string
def get_data_format_from_string(str):
    data_format = {}
    data_format["Float32"]   = 0
    data_format["Float16"]   = 1
    data_format["Bfp8"]      = 2
    data_format["Bfp4"]      = 3
    data_format["Bfp2"]      = 11
    data_format["Float16_b"] = 5
    data_format["Bfp8_b"]    = 6
    data_format["Bfp4_b"]    = 7
    data_format["Bfp2_b"]    = 15
    data_format["Lf8"]       = 10
    data_format["UInt16"]    = 12
    data_format["Int8"]      = 14
    data_format["Tf32"]      = 4
    if str in data_format:
        return data_format[str]
    return None

# gets information about stream buffer in l1 cache from blob
def get_l1_buffer_info_from_blob(device_id, graph, noc0_loc, stream_id, phase):
    buffer_addr = 0
    msg_size = 0
    buffer_size = 0

    stream_loc = (device_id, *noc0_loc, stream_id, phase)
    stream = graph.get_streams(stream_loc).first()

    if stream.root.get("buf_addr"):
        buffer_addr = stream.root.get("buf_addr")
        buffer_size = stream.root.get("buf_size")
        msg_size =stream.root.get("msg_size")
    return buffer_addr, buffer_size, msg_size

# Prints a tile (message) from a given buffer
def dump_message_xy(context, ui_state, tile_id, raw):
    is_tile = raw == 0
    device_id = ui_state['current_device_id']
    graph_name = ui_state ['current_graph_name']
    graph = context.netlist.graph(graph_name)
    current_device = context.devices[device_id]
    noc0_loc, stream_id = (ui_state['current_x'], ui_state['current_y']), ui_state['current_stream_id']
    current_phase = current_device.get_stream_phase (noc0_loc, stream_id)
    try:
        buffer_addr, buffer_size, msg_size = get_l1_buffer_info_from_blob(device_id, graph, noc0_loc, stream_id, current_phase)
    except:
        print (f"{util.CLR_RED}No information{util.CLR_END}")
        return
    print(f"{noc0_loc[0]}-{noc0_loc[1]} buffer_addr: 0x{(buffer_addr):08x} buffer_size: 0x{buffer_size:0x} msg_size:{msg_size}")
    if (buffer_addr >0 and buffer_size>0 and msg_size>0) :
        if (tile_id> 0 and tile_id <= buffer_size/msg_size):
            msg_addr = buffer_addr + (tile_id - 1) * msg_size
            if is_tile:
                # 1. Get the op name through coordinates.
                stream_loc = (device_id, *noc0_loc, stream_id, current_phase)
                stream = graph.get_streams(stream_loc).first()
                if stream is None:
                    util.ERROR (f"Cannot find stream {stream_loc}")
                    return
                buffer = graph.get_buffers(stream.get_buffer_id()).first()
                loc_rc = current_device.noc0_to_rc( noc0_loc )
                op_name = graph.core_coord_to_op_name (loc_rc)

                # 2. Get the operation so we can get the data format
                op = graph.root[op_name]
                assert (buffer.root['md_op_name'] == op_name) # Make sure the op name is the same as the one in the buffer itself

                if buffer.is_input:
                    data_format_str = op['in_df'][0] # FIX: we are picking the first from the list
                else:
                    data_format_str = op['out_df']

                data_format = get_data_format_from_string (data_format_str)

                # 3. Dump the tile
                current_device.dump_tile(noc0_loc, msg_addr, msg_size, data_format)
            else:
                current_device.dump_memory(noc0_loc, msg_addr, msg_size)
        else:
            print(f"Message id should be in range (1, {buffer_size//msg_size})")
    else:
        print("Not enough data in blob.yaml")

def run(args, context, ui_state = None):
    tile_id = int(args[1])
    raw = int(args[2])

    navigation_suggestions = []

    dump_message_xy(context, ui_state, tile_id, raw)

    return navigation_suggestions
