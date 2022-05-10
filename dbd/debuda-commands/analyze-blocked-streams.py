# Traverses all streams and detects the blocked one. It then prints the results.
# It prioritizes the streams that are genuinely blocked, to the ones that are waiting on genuinely 
# blocked cores.

import stream, objects

command_metadata = {
        "short" : "abs",
        "expected_argument_count" : 0,
        "arguments_description" : ": draws a mini map of the current epoch"
    }

def run(args, context):
# def analyze_blocked_streams (graph, device_array, current_x, current_y):
    headers = [ "X-Y", "Op", "Stream", "Type", "Epoch", "Phase", "MSGS_REMAINING", "MSGS_RECEIVED", "Depends on", "State", "Flag" ]
    rows = []

    # 1. Read and analyze data
    device_data = dict()
    active_streams = dict()
    empty_input_streams = dict()

    for i, device in enumerate (context.devices):
        device_data[i] = {
            "device" : device,
            "cores" : { }
        }
        # 1. Read all stream registers
        stream_cache = objects.CachedDictFile (stream.STREAM_CACHE_FILE_NAME)
        all_stream_regs = stream_cache.load_cached (device.read_all_stream_registers, "device.read_all_stream_registers ()")

        # 2. Check where the cores are
        device.get_stream_states(all_stream_regs)

        all_streams_ui_data = dict()
        for stream_loc, stream_regs in all_stream_regs.items():
            all_streams_ui_data[stream_loc] = stream.convert_reg_dict_to_strings(device, stream_regs)

        # 2a. Analyze the data
        for block_loc in device.get_block_noc0_locactions (block_type = "functional_workers"):
            x, y = block_loc[0], block_loc[1]
            has_active_stream = False
            has_empty_inputs = False

            for stream_id in range (0, 64):
                forced_active_stream = x == 1 and y == 1 and stream_id==8

                stream_loc = block_loc + (stream_id, )
                if stream.is_stream_active(all_stream_regs[stream_loc]) or forced_active_stream:
                    has_active_stream = True
                    active_streams[(i, x, y, stream_id)] = stream_loc
                current_phase = int(all_stream_regs[stream_loc]['CURR_PHASE'])
                if current_phase > 0: # Must be configured
                    stream_type_str = device.stream_type(stream_id)["short"]
                    NUM_MSGS_RECEIVED = int(all_stream_regs[stream_loc]['NUM_MSGS_RECEIVED'])
                    if stream_type_str == "input" and NUM_MSGS_RECEIVED == 0:
                        has_empty_inputs = True
                        empty_input_streams[(i, x, y, stream_id)] = stream_loc

            device_data[i]["cores"][block_loc] = {\
                "fan_in_cores" : [],\
                "has_active_stream" : has_active_stream,\
                "has_empty_inputs" : has_empty_inputs\
            }

        # 2b. Find stream dependencies
        active_core_rc_list = [ device.noc0_to_rc( active_stream[1], active_stream[2] ) for active_stream in active_streams ]
        active_core_noc0_list = [ ( active_stream[1], active_stream[2] ) for active_stream in active_streams ]
        for active_core_rc in active_core_rc_list:
            fan_in_cores_rc = get_fanin_cores_rc (active_core_rc)
            active_core_noc0 = device.rc_to_noc0 (active_core_rc[0], active_core_rc[1])
            # print (f"fan_in_cores_rc for {active_core_rc}: {fan_in_cores_rc}")
            fan_in_cores_noc0 = [ device.rc_to_noc0 (rc[0], rc[1]) for rc in fan_in_cores_rc ]
            device_data[i]["cores"][active_core_noc0[0]][active_core_noc0[1]]["fan_in_cores"] = fan_in_cores_noc0

        # 3. Print the output
        last_core_loc = None

        for block_loc in device.get_block_noc0_locactions (block_type = "functional_workers"):
            x, y = block_loc[0], block_loc[1]
            stream_loc = block_loc + (stream_id,)
            has_active_stream = device_data[i]["cores"][block_loc]["has_active_stream"]
            has_empty_inputs = device_data[i]["cores"][block_loc]["has_empty_inputs"]
            if has_active_stream:
                for stream_id in range (0, 64):
                    current_phase = int(all_stream_regs[stream_loc]['CURR_PHASE'])
                    if current_phase > 0:
                        epoch_id = current_phase>>10
                        stream_type_str = stream_type(stream_id)["short"]
                        stream_active = is_stream_active(all_stream_regs[stream_loc])
                        NUM_MSGS_RECEIVED = int(all_stream_regs[stream_loc]['NUM_MSGS_RECEIVED'])
                        CURR_PHASE_NUM_MSGS_REMAINING = int(all_stream_regs[stream_loc]['CURR_PHASE_NUM_MSGS_REMAINING'])
                        graph_name = EPOCH_ID_TO_GRAPH_NAME[epoch_id]
                        op = core_coord_to_op_name(graph_name, x, y)
                        core_loc = f"{x}-{y}"
                        fan_in_cores = device_data[i]['cores'][block_loc]['fan_in_cores']
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


