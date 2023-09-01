"""
.. code-block::
   :caption: Example

        Current epoch:0(test_op) device:0 core:5-3 rc:2,4 stream:8 > t 1 0
        5-3 buffer_addr: 0x0003b000 buffer_size: 0x10400 msg_size:2080
         0.0976   0.1857   0.4302   0.6885   0.2054   0.7158   0.0897   0.6943  -0.1526   0.2471   0.2917  -0.2312  -0.1248  -0.4048   0.7832  -0.8862   0.9272  -0.4546  -0.2330  -0.0446   0.5830   0.6240   0.0578  -0.0400   0.1360  -0.2144   0.8511   0.6719  -0.8579  -0.3252  -0.8257   0.2961 
        -0.9595  -0.2634   0.6650   0.9141   0.5562  -0.7192   0.7397   0.7397   0.9570  -0.0528   0.5981   0.6016  -0.0770   0.0410   0.5610   0.3577  -0.7632   0.4412   0.2798   0.1639  -0.7129   0.0747   0.8892   0.5171   0.0437  -0.7881  -0.1707  -0.0528  -0.4707  -0.6270   0.5483   0.4736 
        -0.0876  -0.5669   0.1368  -0.7295  -0.9624  -0.3516   0.2352  -0.7002   0.2241  -0.5552   0.2338  -0.2269   0.8872   0.8052   0.3635  -0.1001  -0.2808   0.2261  -0.1259   0.8047   0.3950  -0.8013  -0.8794   0.9395   0.3335   0.3062   0.3411  -0.6577  -0.5791  -0.2837  -0.7417   0.5010 
        ...
"""
from tabulate import tabulate
import tt_util as util
from tt_coordinate import OnChipCoordinate

command_metadata = {
    "short" : "t",
    "type" : "high-level",
    "expected_argument_count" : [ 2 ],
    "arguments" : "tile_id raw",
    "description" : "Prints tile for the current stream in the currently active phase. If raw=1, it prints raw bytes."
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
def get_l1_buffer_info_from_blob(device_id, graph, loc, stream_id, phase):
    buffer_addr = 0
    msg_size = 0
    buffer_size = 0

    stream_loc = (device_id, *loc.to('nocTr'), stream_id, phase)
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
    loc, stream_id = ui_state['current_loc'], ui_state['current_stream_id']
    current_phase = current_device.get_stream_phase (loc, stream_id)
    try:
        buffer_addr, buffer_size, msg_size = get_l1_buffer_info_from_blob(device_id, graph, loc, stream_id, current_phase)
    except:
        util.ERROR (f"No information")
        return
    print(f"{loc.to_str()} buffer_addr: 0x{(buffer_addr):08x} buffer_size: 0x{buffer_size:0x} msg_size:{msg_size}")
    if (buffer_addr >0 and buffer_size>0 and msg_size>0) :
        if (tile_id> 0 and tile_id <= buffer_size/msg_size):
            msg_addr = buffer_addr + (tile_id - 1) * msg_size
            if is_tile:
                # 1. Get the op name through coordinates.
                stream_loc = (device_id, *loc.to('nocTr'), stream_id, current_phase)
                stream = graph.get_streams(stream_loc).first()
                if stream is None:
                    util.ERROR (f"Cannot find stream {stream_loc}")
                    return
                bid = stream.get_buffer_id()
                if bid is None:
                    util.ERROR (f"Cannot find buffer for stream {stream_loc}")
                    return
                buffer = graph.buffers[bid]
                op_name = graph.location_to_op_name (loc)

                # 2. Get the operation so we can get the data format
                op = graph.root[op_name]
                assert (buffer.root['md_op_name'] == op_name) # Make sure the op name is the same as the one in the buffer itself

                if buffer.is_input:
                    data_format_str = op['in_df'][0] # FIX: we are picking the first from the list
                else:
                    data_format_str = op['out_df']

                data_format = get_data_format_from_string (data_format_str)

                # 3. Dump the tile
                current_device.dump_tile(loc, msg_addr, msg_size, data_format)
            else:
                current_device.dump_memory(loc, msg_addr, msg_size)
        else:
            util.ERROR(f"Message id should be in range (1, {buffer_size//msg_size})")
    else:
        util.ERROR("Not enough data in blob.yaml")

def run(args, context, ui_state = None):
    tile_id = int(args[1])
    raw = int(args[2])

    navigation_suggestions = []

    dump_message_xy(context, ui_state, tile_id, raw)

    return navigation_suggestions
