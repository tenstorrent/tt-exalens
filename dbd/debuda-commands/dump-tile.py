# Traverses all streams and detects the blocked one. It then prints the results.
# It prioritizes the streams that are genuinely blocked, to the ones that are waiting on genuinely 
# blocked cores.
from tabulate import tabulate
import tt_util as util

command_metadata = {
    "short" : "t",
    "expected_argument_count" : 2,
    "arguments_description" : "tile_id, raw: prints tile for current stream in currently active phase. If raw=1, prints raw bytes"
}

# gets information about stream buffer in l1 cache from blob
def get_l1_buffer_info_from_blob(device_id, graph, x, y, stream_id, phase):
    buffer_addr = 0
    msg_size = 0
    buffer_size = 0

    stream_loc = (device_id, x, y, stream_id, phase)
    stream = graph.streams[stream_loc]

    if stream.root.get("buf_addr"):
        buffer_addr = stream.root.get("buf_addr")
        buffer_size = stream.root.get("buf_size")
        msg_size =stream.root.get("msg_size")
    return buffer_addr, buffer_size, msg_size

# Prints a tile (message) from a given buffer
def dump_message_xy(context, ui_state, tile_id, raw):
    device_id = ui_state['current_device_id']
    epoch_id = ui_state ['current_epoch_id']
    graph_name = context.netlist.epoch_id_to_graph_name(epoch_id)
    graph = context.netlist.graph(graph_name)
    current_device = context.devices[device_id]
    x, y, stream_id = ui_state['current_x'], ui_state['current_y'], ui_state['current_stream_id']
    current_phase = current_device.get_stream_phase (x, y, stream_id)
    try:
        buffer_addr, buffer_size, msg_size = get_l1_buffer_info_from_blob(device_id, graph, x, y, stream_id, current_phase)
    except:
        print (f"{util.CLR_RED}No information{util.CLR_END}")
        return
    print(f"{x}-{y} buffer_addr: 0x{(buffer_addr):08x} buffer_size: 0x{buffer_size:0x} msg_size:{msg_size}")
    if (buffer_addr >0 and buffer_size>0 and msg_size>0) :
        if (tile_id> 0 and tile_id <= buffer_size/msg_size):
            current_device.dump_memory(x, y, buffer_addr + (tile_id - 1) * msg_size, msg_size )
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
