# Traverses all streams and detects the blocked one. It then prints the results.
# It prioritizes the streams that are genuinely blocked, to the ones that are waiting on genuinely 
# blocked cores.
from tabulate import tabulate
import tt_stream, tt_objects, tt_util as util

command_metadata = {
        "short" : "abs",
        "expected_argument_count" : 0,
        "arguments_description" : ": draws a mini map of the current epoch"
    }

def run(args, context, ui_state = None):
    navigation_suggestions = []

    headers = [ "X-Y", "Op", "Stream", "Type", "Epoch", "Phase", "MSGS_REMAINING", "MSGS_RECEIVED", "Depends on", "State", "Flag" ]
    rows = []

    # 1. Read and analyze data
    device_data = dict()
    active_streams = dict()
    empty_input_streams = dict()

    netlist = context.netlist

    for device_id, device in enumerate (context.devices):
        device_data[device_id] = {
            "device" : device,
            "cores" : { }
        }
        # 1. Read all stream registers
        stream_cache = tt_objects.CachedDictFile (tt_stream.STREAM_CACHE_FILE_NAME)
        all_stream_regs = stream_cache.load_cached (device.read_all_stream_registers, "device.read_all_stream_registers ()")

        # 2. Check where the programmed streams are
        programmed_streams = device.get_programmed_stream_locations(all_stream_regs)

        # Find epochs for each stream
        epochs = { device.stream_epoch (stream_regs) for loc, stream_regs in all_stream_regs.items() if loc in programmed_streams }
        print (f"Stream epochs: {epochs}")

        working_epoch_id = min(epochs)
        working_graph_name = netlist.epoch_id_to_graph_name (working_epoch_id)
        graph = netlist.graph (working_graph_name)

        all_streams_ui_data = dict()
        for stream_loc, stream_regs in all_stream_regs.items():
            all_streams_ui_data[stream_loc] = tt_stream.convert_reg_dict_to_strings(device, stream_regs)

        # 2a. Analyze the data
        for block_loc in device.get_block_locations (block_type = "functional_workers"):
            x, y = block_loc[0], block_loc[1]
            has_active_stream = False
            has_empty_inputs = False

            for stream_id in range (0, 64):
                stream_loc = block_loc + (stream_id, )
                if device.is_stream_active(all_stream_regs[stream_loc]):
                    has_active_stream = True
                    active_streams[(device_id, x, y, stream_id)] = stream_loc
                current_phase = int(all_stream_regs[stream_loc]['CURR_PHASE'])
                if current_phase > 0: # Must be configured
                    stream_type_str = device.stream_type(stream_id)["short"]
                    NUM_MSGS_RECEIVED = int(all_stream_regs[stream_loc]['NUM_MSGS_RECEIVED'])
                    if stream_type_str == "input" and NUM_MSGS_RECEIVED == 0:
                        has_empty_inputs = True
                        empty_input_streams[(device_id, x, y, stream_id)] = stream_loc

            device_data[device_id]["cores"][block_loc] = {\
                "fan_in_cores" : [],\
                "has_active_stream" : has_active_stream,\
                "has_empty_inputs" : has_empty_inputs\
            }

        # 2b. Find stream dependencies
        active_core_rc_list = [ device.noc0_to_rc( active_stream[1], active_stream[2] ) for active_stream in active_streams ]
        active_core_noc0_list = [ ( active_stream[1], active_stream[2] ) for active_stream in active_streams ]
        for active_core_rc in active_core_rc_list:
            fan_in_cores_rc = graph.get_fanin_cores_rc (active_core_rc)
            active_core_noc0 = device.rc_to_noc0 (active_core_rc[0], active_core_rc[1])
            # print (f"fan_in_cores_rc for {active_core_rc}: {fan_in_cores_rc}")
            fan_in_cores_noc0 = [ device.rc_to_noc0 (rc[0], rc[1]) for rc in fan_in_cores_rc ]
            device_data[device_id]["cores"][active_core_noc0]["fan_in_cores"] = fan_in_cores_noc0

        # 3. Print the output
        last_core_loc = None

        for block_loc in device.get_block_locations (block_type = "functional_workers"):
            x, y = block_loc[0], block_loc[1]
            has_active_stream = device_data[device_id]["cores"][block_loc]["has_active_stream"]
            has_empty_inputs = device_data[device_id]["cores"][block_loc]["has_empty_inputs"]
            if has_active_stream:
                for stream_id in range (0, 64):
                    stream_loc = block_loc + (stream_id,)
                    current_phase = int(all_stream_regs[stream_loc]['CURR_PHASE'])
                    if current_phase > 0:
                        epoch_id = current_phase>>10
                        stream_type_str = device.stream_type(stream_id)["short"]
                        stream_active = device.is_stream_active(all_stream_regs[stream_loc])
                        NUM_MSGS_RECEIVED = int(all_stream_regs[stream_loc]['NUM_MSGS_RECEIVED'])
                        CURR_PHASE_NUM_MSGS_REMAINING = int(all_stream_regs[stream_loc]['CURR_PHASE_NUM_MSGS_REMAINING'])
                        op = "N/A" # graph.core_coord_to_op_name(graph_name, x, y)
                        core_loc = f"{x}-{y}"
                        fan_in_cores = device_data[device_id]['cores'][block_loc]['fan_in_cores']
                        fan_in_cores_str = ""
                        if last_core_loc != core_loc:
                            for fic_noc0 in fan_in_cores:
                                if fic_noc0 in active_core_noc0_list:
                                    fan_in_cores_str += f"{fic_noc0[0]}-{fic_noc0[1]} "
                        flag = f"{util.CLR_WARN}All core inputs ready, but no output generated{util.CLR_END}" if not has_empty_inputs and last_core_loc != core_loc else ""
                        row = [ core_loc if last_core_loc != core_loc else "", op if last_core_loc != core_loc else "", stream_id, stream_type_str, epoch_id, current_phase, CURR_PHASE_NUM_MSGS_REMAINING, NUM_MSGS_RECEIVED, fan_in_cores_str, f"Active" if stream_active else "", flag ]
                        last_core_loc = core_loc
                        rows.append (row)
    if len(rows) > 0:
        print (tabulate(rows, headers=headers))
    else:
        print ("No blocked streams detected")

    return navigation_suggestions

# Detects potential problems within all chip streams, and prints a summary
def stream_summary(chip, x_coords, y_coords, streams, short=False):
    active_streams = {}
    bad_streams = []
    gsync_hung = {}
    ncrisc_done = {}

    # Detect problems
    for x in x_coords:
        active_streams[x] = {}
        gsync_hung[x] = {}
        ncrisc_done[x] = {}
        for y in y_coords:
            active_streams[x][y] = []
            for stream_id in range (0, 64):
                if is_stream_active(streams[x][y][stream_id]):
                    active_streams[x][y].append(stream_id)
                if is_bad_stream(streams[x][y][stream_id]):
                    bad_streams.append([x,y,stream_id])
            gsync_hung[x][y] = is_gsync_hung(chip, x, y)
            ncrisc_done[x][y] = is_ncrisc_done(chip, x, y)

    # Print streams that are not idle
    all_streams_done = True
    headers = [ "X-Y", "Op", "Stream", "Type", "Epoch", "Phase", "State", "CURR_PHASE_NUM_MSGS_REMAINING", "NUM_MSGS_RECEIVED" ]
    rows = []

    for x in x_coords:
        for y in y_coords:
            if len(active_streams[x][y]) != 0:
                first_stream = True

                for i in range(len(active_streams[x][y])):
                    xy = f"{x}-{y}" if first_stream else ""
                    first_stream = False
                    stream_id=active_streams[x][y][i]
                    current_phase = int(streams[x][y][stream_id]['CURR_PHASE'])
                    epoch_id = current_phase>>10
                    stream_type_str = stream_type(stream_id)["short"]
                    op = core_coord_to_op_name(EPOCH_ID_TO_GRAPH_NAME[epoch_id], x, y)
                    row = [ xy, op, stream_id, stream_type_str, epoch_id, current_phase, f"{util.CLR_WARN}Active{util.CLR_END}", int(streams[x][y][stream_id]['CURR_PHASE_NUM_MSGS_REMAINING']), int(streams[x][y][stream_id]['NUM_MSGS_RECEIVED']) ]
                    rows.append (row)
                    all_streams_done = False

    if not all_streams_done:
        print (tabulate(rows, headers=headers))
    if all_streams_done:
        print("  No streams appear hung. If the test hung, some of the streams possibly did not get any tiles.")

    # Print streams in bad state
    if len(bad_streams) != 0:
        print()
        print("The following streams are in a bad state (have an assertion in DEBUG_STATUS[1], or DEBUG_STATUS[2] indicates a hang):")
        for i in range(len(bad_streams)):
            bad_stream_x = bad_streams[i][0]
            bad_stream_y = bad_streams[i][1]
            bad_stream_id = bad_streams[i][2]
            print(f"\t x={bad_stream_x:02d}, y={bad_stream_y:02d}, stream_id={bad_stream_id:02d}")

    # Print gsync_hung cores
    for x in x_coords:
        for y in y_coords:
            if gsync_hung[x][y]:
                print(f"Global sync hang: x={x:02d}, y={y:02d}")

    # Print NC Riscs that are not idle
    if all_streams_done: # Only do this if all streams are done
        ncriscs_not_idle_count = 0
        for y in y_coords:
            for x in x_coords:
                if not ncrisc_done[x][y]:
                    if ncriscs_not_idle_count == 0: # First output
                        print("NCRISCs not idle: ")
                    ncriscs_not_idle_count += 1
                    print(f"{x:02d}-{y:02d}", end=" ")
                    if ncriscs_not_idle_count % 12 == 0:
                        print()
        if ncriscs_not_idle_count > 0:
            print()