# Traverses all streams and detects the blocked one. It then prints the results.
# It prioritizes the streams that are genuinely blocked, to the ones that are waiting on genuinely 
# blocked cores.
from tabulate import tabulate
import tt_stream, tt_netlist, tt_util as util

command_metadata = {
        "short" : "abs",
        "expected_argument_count" : [0,1],
        "arguments_description" : "verbosity [0-1]: reads stream information from the devices and highlights blocked streams (if verbosity is 1, print more detail)"
    }

def run(args, context, ui_state = None):
    if len(args) == 2:
        verbosity = int(args[1])
    else:
        verbosity = 0

    navigation_suggestions = []

    headers = [ "X-Y", "Op", "Stream", "Type", "Epoch", "Phase", "MSGS_REMAINING", "MSGS_RECEIVED", "Depends on", "State", "Flag" ]
    rows = []

    # 1. Read and analyze data
    device_data = dict()
    active_streams = dict()
    empty_input_streams = dict()

    netlist = context.netlist

    for device_id, device in enumerate (context.devices):
        util.INFO (f"Analyzing device {device_id + 1}/{len(context.devices)}")
        device_data[device_id] = {
            "device" : device,
            "cores" : { }
        }
        # 1. Read all stream registers
        all_stream_regs = device.read_all_stream_registers ()

        # Find epochs for each stream
        epochs = set()
        epoch_to_graph_map = dict()
        for loc, stream_regs in all_stream_regs.items():
            epoch_id = device.stream_epoch (stream_regs)
            if epoch_id not in epochs:
                epochs.add (epoch_id)
            graph_name = netlist.epoch_id_to_graph_name (epoch_id)
            if graph_name is None:
                util.ERROR (f"Stream at {loc} is in epoch {epoch_id}, which does not exist in the netlist")
            else:
                epoch_to_graph_map[epoch_id] = netlist.graph (graph_name)

        if len(epochs) == 0:
            util.INFO (f"Device {device_id} has no programmed streams. Cannot determine the current epoch.")
            continue
        elif len(epochs) > 1:
            util.WARN (f"The streams within the device are in the following set of epochs: {epochs}.")

        working_epoch_id = list(epochs)[0]
        working_graph_name = netlist.epoch_id_to_graph_name (working_epoch_id)
        device_graph = netlist.graph (working_graph_name)
        all_streams_ui_data = dict()
        for stream_loc, stream_regs in all_stream_regs.items():
            all_streams_ui_data[stream_loc] = tt_stream.convert_reg_dict_to_strings(device, stream_regs)

        issues_sets = {
            "bad_stream" : set(),
            "gsync_hung" : set(),
            "ncrisc_not_done" : set()
        }

        # 2a. Analyze the data
        all_streams_done = True
        for block_loc in device.get_block_locations (block_type = "functional_workers"):
            has_active_stream = False
            has_empty_inputs = False

            for stream_id in range (0, 64):
                stream_loc = block_loc + (stream_id, )
                if device.is_stream_active(all_stream_regs[stream_loc]):
                    has_active_stream = True
                    active_streams[(device_id, *block_loc, stream_id)] = stream_loc
                    all_streams_done = False
                current_phase = int(all_stream_regs[stream_loc]['CURR_PHASE'])
                if current_phase > 0: # Must be configured
                    stream_type_str = device.stream_type(stream_id)["short"]
                    NUM_MSGS_RECEIVED = int(all_stream_regs[stream_loc]['NUM_MSGS_RECEIVED'])
                    if stream_type_str == "input" and NUM_MSGS_RECEIVED == 0:
                        has_empty_inputs = True
                        empty_input_streams[(device_id, *block_loc, stream_id)] = stream_loc

                if device.is_bad_stream (all_stream_regs[stream_loc]):
                    issues_sets["bad_stream"].add (stream_loc)

            if device.is_gsync_hung (block_loc):
                issues_sets["gsync_hung"].add (block_loc)
            if not device.is_ncrisc_done (block_loc):
                issues_sets["ncrisc_not_done"].add (block_loc)

            device_data[device_id]["cores"][block_loc] = {\
                "fan_in_cores" : [],\
                "has_active_stream" : has_active_stream,\
                "has_empty_inputs" : has_empty_inputs\
            }

        # 2b. Find stream dependencies
        active_core_rc_list = [ device.noc0_to_rc( ( active_stream[1], active_stream[2] ) ) for active_stream in active_streams ]
        active_core_noc0_list = [ ( active_stream[1], active_stream[2] ) for active_stream in active_streams ]
        for active_core_rc in active_core_rc_list:
            fan_in_cores_rc = device_graph.get_fanin_cores_rc (active_core_rc)
            active_core_noc0 = device.rc_to_noc0 (active_core_rc)
            # print (f"fan_in_cores_rc for {active_core_rc}: {fan_in_cores_rc}")
            fan_in_cores_noc0 = [ device.rc_to_noc0 (rc) for rc in fan_in_cores_rc ]
            device_data[device_id]["cores"][active_core_noc0]["fan_in_cores"] = fan_in_cores_noc0

        # 3. Print the summary of blocked streams
        last_core_loc = None

        for block_loc in device.get_block_locations (block_type = "functional_workers"):
            x, y = block_loc[0], block_loc[1]
            rc_loc = device.noc0_to_rc (block_loc)
            has_active_stream = device_data[device_id]["cores"][block_loc]["has_active_stream"]
            has_empty_inputs = device_data[device_id]["cores"][block_loc]["has_empty_inputs"]
            if has_active_stream:
                for stream_id in range (0, 64):
                    add_stream_to_navigation_suggestions = False
                    stream_loc = block_loc + (stream_id,)
                    current_phase = int(all_stream_regs[stream_loc]['CURR_PHASE'])
                    if current_phase > 0:
                        epoch_id = current_phase>>10
                        stream_type_str = device.stream_type(stream_id)["short"]
                        stream_active = device.is_stream_active(all_stream_regs[stream_loc])
                        NUM_MSGS_RECEIVED = int(all_stream_regs[stream_loc]['NUM_MSGS_RECEIVED'])
                        CURR_PHASE_NUM_MSGS_REMAINING = int(all_stream_regs[stream_loc]['CURR_PHASE_NUM_MSGS_REMAINING'])

                        op=f"Unknown opoch_id {epoch_id}"
                        if epoch_id in epoch_to_graph_map:
                            graph = epoch_to_graph_map[epoch_id]
                            op = graph.core_coord_to_full_op_name(rc_loc)
                        core_loc = f"{x}-{y}"
                        fan_in_cores = device_data[device_id]['cores'][block_loc]['fan_in_cores']
                        depends_on_str = ""
                        flag = ""
                        if last_core_loc != core_loc: # Do it only once per core
                            # a. Note dependencies
                            for fic_noc0 in fan_in_cores:
                                if fic_noc0 in active_core_noc0_list:
                                    depends_on_str += f"{fic_noc0[0]}-{fic_noc0[1]} "
                            # b. Flags
                            if not has_empty_inputs:
                                flag = f"{util.CLR_WARN}All core inputs ready, but no output generated{util.CLR_END}"
                                add_stream_to_navigation_suggestions = True

                        row = [ core_loc if last_core_loc != core_loc else "", op if last_core_loc != core_loc else "", stream_id, stream_type_str, epoch_id, current_phase, CURR_PHASE_NUM_MSGS_REMAINING, NUM_MSGS_RECEIVED, depends_on_str, f"Active" if stream_active else "", flag ]
                        last_core_loc = core_loc
                        if verbosity > 0 or flag != "":
                            rows.append (row)
                        if verbosity and stream_active:
                            add_stream_to_navigation_suggestions = True

                    if add_stream_to_navigation_suggestions:
                        navigation_suggestions.append (\
                            { 'description': 'Go to stream',
                                'cmd' : f"s {x} {y} {stream_id}",
                                'loc' : (x, y)
                            })



        # 4. Print any issues
        if len (issues_sets["bad_stream"]) > 0:
            print ("Bad streams (check DEBUG_STATUS registers):")
            for loc in issues_sets["bad_stream"]:
                print(f"\t x={loc[0]:02d}, y={loc[1]:02d}, stream_id={loc[2]:02d}")
        if len (issues_sets["gsync_hung"]) > 0:
            print ("Global sync hang:")
            for loc in issues_sets["gsync_hung"]:
                print(f"{loc[0]}-{loc[1]}", end = ' ')
            print()
        if all_streams_done and len(issues_sets["ncrisc_not_done"]) > 0:
            print (device.render (options='rc', emphasize_noc0_loc_list = issues_sets.get ("ncrisc_not_done", set()), emphasize_explanation="NCrisc not done"))
            print()

    if len(rows) > 0:
        print (tabulate(rows, headers=headers))
    else:
        print ("No blocked streams detected")

    return navigation_suggestions
