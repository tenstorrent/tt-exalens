#!/usr/bin/env python3
"""
debuda parses the build output files and probes the silicon to determine status of a buda run.
"""
import sys, os, argparse, time, traceback, atexit, fnmatch, importlib
from tabulate import tabulate
import tt_util as util, tt_device, tt_grayskull, tt_netlist, tt_stream
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML

parser = argparse.ArgumentParser(description=__doc__ + tt_device.STUB_HELP)
parser.add_argument('output_dir', type=str, nargs='?', default=None, help='Output directory of a buda run. If left blank, the most recent subdirectory of tt_build/ will be used')
parser.add_argument('--netlist',  type=str, required=False, default=None, help='Netlist file to import. If not supplied, the most recent subdirectory of tt_build/ will be used')
parser.add_argument('--commands', type=str, required=False, help='Execute a set of commands separated by ;')
parser.add_argument('--stream-cache', action='store_true', default=False, help=f'If file "{tt_stream.STREAM_CACHE_FILE_NAME}" exists, the stream data will be loaded from it. If the file does not exist, it will be created and populated with the stream data')
parser.add_argument('--server-cache', type=str, default='off', help=f'Directs communication with Debuda Server. When "off", all device reads are done through the server. When set to "through", attempt to read from cache first. When "on", all reads are from cache only.')
parser.add_argument('--debug-debuda-stub', action='store_true', default=False, help=f'Prints all transactions on PCIe. Also, starts debuda-stub with --debug to print transfers.')
parser.add_argument('--verbose', action='store_true', default=False, help=f'Prints additional information.')
args = parser.parse_args()
util.args = args
import pprint
pp = pprint.PrettyPrinter(indent=4)

### BUILT-IN COMMANDS

# Find occurrences of buffer with ID 'buffer_id' across all epochs, and print the structures that reference them
# Supply ui_state['current_epoch_id']=None, to show details in all epochs
def print_buffer_data (cmd, context):
    buffer_id = int(cmd[1])

    for epoch_id in context.netlist.epoch_ids():
        graph_name = context.netlist.epoch_id_to_graph_name(epoch_id)
        graph = context.netlist.graph(graph_name)
        buffer = graph.get_buffer(buffer_id)
        if buffer:
            util.print_columnar_dicts ([buffer.root], [f"{util.CLR_INFO}Epoch {epoch_id}{util.CLR_END}"])

        navigation_suggestions = [ ]
        for p in graph.pipes:
            pipe = graph.get_pipe(p)
            if buffer_id in pipe.root["input_list"]:
                print (f"( {util.CLR_BLUE}Input{util.CLR_END} of pipe {pipe.id()} )")
                navigation_suggestions.append ({ 'cmd' : f"p {pipe.id()}", 'description' : "Show pipe" })
            if buffer_id in pipe.root["output_list"]:
                print (f"( {util.CLR_BLUE}Output{util.CLR_END} of pipe {pipe.id()} )")
                navigation_suggestions.append ({ 'cmd' : f"p {pipe.id()}", 'description' : "Show pipe" })

    return navigation_suggestions

# Find occurrences of pipe with ID 'pipe_id' across all epochs, and print the structures that reference them
# Supply current_epoch_id=None, to show details in all epochs
def print_pipe_data (cmd, context):
    pipe_id = int(cmd[1])

    for epoch_id in context.netlist.epoch_ids():
        graph_name = context.netlist.epoch_id_to_graph_name(epoch_id)
        graph = context.netlist.graph(graph_name)
        pipe = graph.get_pipe(pipe_id)
        if pipe:
            util.print_columnar_dicts ([pipe.root], [f"{util.CLR_INFO}Epoch {epoch_id}{util.CLR_END}"])

        navigation_suggestions = [ ]
        for input_buffer in pipe.root['input_list']:
            navigation_suggestions.append ({ 'cmd' : f"b {input_buffer}", 'description' : "Show src buffer" })
        for input_buffer in pipe.root['output_list']:
            navigation_suggestions.append ({ 'cmd' : f"b {input_buffer}", 'description' : "Show dest buffer" })

    return navigation_suggestions

# Prints information on DRAM queues
def print_dram_queue_summary (cmd, context, ui_state = None): # graph, chip_array):
    if ui_state is not None:
        epoch_id_list = [ ui_state["current_epoch_id"] ]
    else:
        epoch_id_list = context.netlist.epoch_ids()

    table = []
    for epoch_id in epoch_id_list:
        print (f"{util.CLR_INFO}DRAM queues for epoch %d{util.CLR_END}" % epoch_id)
        graph_name = context.netlist.epoch_id_to_graph_name (epoch_id)
        graph = context.netlist.graph(graph_name)
        device_id = context.netlist.graph_name_to_device_id(graph_name)

        for buffer_id, buffer in graph.buffers.items():
            buffer_data = buffer.root
            if buffer_data["dram_buf_flag"] != 0 or buffer_data["dram_io_flag"] != 0 and buffer_data["dram_io_flag_is_remote"] == 0 and not buffer.replicated:
                dram_chan = buffer_data["dram_chan"]
                dram_addr = buffer_data['dram_addr']
                dram_loc = tt_grayskull.CHANNEL_TO_DRAM_LOC[dram_chan]
                rdptr = tt_device.PCI_IFC.pci_read_xy (device_id, dram_loc[0], dram_loc[1], 0, dram_addr)
                wrptr = tt_device.PCI_IFC.pci_read_xy (device_id, dram_loc[0], dram_loc[1], 0, dram_addr + 4)
                slot_size_bytes = buffer_data["size_tiles"] * buffer_data["tile_size"]
                queue_size_bytes = slot_size_bytes * buffer_data["q_slots"]
                occupancy = (wrptr - rdptr) if wrptr >= rdptr else wrptr - (rdptr - buffer_data["q_slots"])

                input_buffer_op_name_list = []
                for other_buffer_id in graph.get_connected_buffers([buffer.id()], 'input'):
                    input_buffer_op_name_list.append (graph.get_buffer(other_buffer_id).root["md_op_name"])
                output_buffer_op_name_list = []
                for other_buffer_id in graph.get_connected_buffers([buffer.id()], 'output'):
                    output_buffer_op_name_list.append (graph.get_buffer(other_buffer_id).root["md_op_name"])

                input_ops = f"{' '.join (input_buffer_op_name_list)}"
                output_ops = f"{' '.join (output_buffer_op_name_list)}"
                table.append ([ buffer_id, buffer_data["md_op_name"], input_ops, output_ops, buffer_data["dram_buf_flag"], buffer_data["dram_io_flag"], dram_chan, f"0x{dram_addr:x}", f"{rdptr}", f"{wrptr}", occupancy, buffer_data["q_slots"], queue_size_bytes ])

    print (tabulate(table, headers=["Buffer ID", "Op", "Input Ops", "Output Ops", "dram_buf_flag", "dram_io_flag", "Channel", "Address", "RD ptr", "WR ptr", "Occupancy", "Slots", "Size [bytes]"] ))

# Prints the queues residing in host's memory.
def print_host_queue_summary (cmd, context, ui_state):
    if ui_state is not None:
        epoch_id_list = [ ui_state["current_epoch_id"] ]
    else:
        epoch_id_list = context.netlist.epoch_ids()

    table = []
    for epoch_id in epoch_id_list:
        graph_name = context.netlist.epoch_id_to_graph_name (epoch_id)
        graph = context.netlist.graph(graph_name)
        device_id = context.netlist.graph_name_to_device_id(graph_name)

        for buffer_id, buffer in graph.buffers.items():
            buffer_data = buffer.root
            if buffer_data["dram_io_flag_is_remote"] != 0:
                dram_addr = buffer_data['dram_addr']
                if dram_addr >> 29 == device_id:
                    rdptr = tt_device.host_dma_read (dram_addr)
                    wrptr = tt_device.host_dma_read (dram_addr + 4)
                    slot_size_bytes = buffer_data["size_tiles"] * buffer_data["tile_size"]
                    queue_size_bytes = slot_size_bytes * buffer_data["q_slots"]
                    occupancy = (wrptr - rdptr) if wrptr >= rdptr else wrptr - (rdptr - buffer_data["q_slots"])
                    table.append ([ buffer_id, buffer_data["dram_buf_flag"], buffer_data["dram_io_flag"], f"0x{dram_addr:x}", f"{rdptr}", f"{wrptr}", occupancy, buffer_data["q_slots"], queue_size_bytes ])

    print (f"{util.CLR_INFO}Host queues (where dram_io_flag_is_remote!=0) for epoch %d {util.CLR_END}" % epoch_id)
    if len(table) > 0:
        print (tabulate(table, headers=["Buffer name", "dram_buf_flag", "dram_io_flag", "Address", "RD ptr", "WR ptr", "Occupancy", "Q slots", "Q Size [bytes]"] ))
    else:
        print ("No host queues found")

# Prints epoch queues
def print_epoch_queue_summary (cmd, context, ui_state):
    epoch_id = ui_state["current_epoch_id"]

    graph_name = context.netlist.epoch_id_to_graph_name (epoch_id)
    graph = context.netlist.graph(graph_name)
    device_id = context.netlist.graph_name_to_device_id(graph_name)
    epoch_device = context.devices[device_id]

    print (f"{util.CLR_INFO}Epoch queues for epoch %d, device id {device_id}{util.CLR_END}" % epoch_id)

    # From tt_epoch_dram_manager::tt_epoch_dram_manager and following the constants
    GridSizeRow = 16
    GridSizeCol = 16
    EPOCH_Q_NUM_SLOTS = 32
    epoch0_start_table_size_bytes = GridSizeRow*GridSizeCol*(EPOCH_Q_NUM_SLOTS*2+8)*4
    # DRAM_CHANNEL_CAPACITY_BYTES  = 1024 * 1024 * 1024
    DRAM_PERF_SCRATCH_SIZE_BYTES =   40 * 1024 * 1024
    # DRAM_HOST_MMIO_SIZE_BYTES    =  256 * 1024 * 1024
    reserved_size_bytes = DRAM_PERF_SCRATCH_SIZE_BYTES - epoch0_start_table_size_bytes

    chip_id = 0
    chip_id += 1

    dram_chan = 0 # CHECK: This queue is always in channel 0
    dram_loc = epoch_device.get_block_locations (block_type = "dram")[dram_chan]

    table=[]
    for loc in epoch_device.get_block_locations (block_type = "functional_workers"):
        y, x = loc[0], loc[1] # FIX: This is backwards - check.
        EPOCH_QUEUE_START_ADDR = reserved_size_bytes
        offset = (16 * x + y) * ((EPOCH_Q_NUM_SLOTS*2+8)*4)
        dram_addr = EPOCH_QUEUE_START_ADDR + offset
        rdptr = tt_device.PCI_IFC.pci_read_xy (device_id, dram_loc[0], dram_loc[1], 0, dram_addr)
        wrptr = tt_device.PCI_IFC.pci_read_xy (device_id, dram_loc[0], dram_loc[1], 0, dram_addr + 4)
        occupancy = (wrptr - rdptr) if wrptr >= rdptr else wrptr - (rdptr - EPOCH_Q_NUM_SLOTS)
        if occupancy > 0:
            table.append ([ f"{x}-{y}", f"0x{dram_addr:x}", f"{rdptr}", f"{wrptr}", occupancy ])

    if len(table) > 0:
        print (tabulate(table, headers=["Location", "Address", "RD ptr", "WR ptr", "Occupancy" ] ))
    else:
        print ("No epoch queues have occupancy > 0")

    util.WARN ("WIP: This results of this function need to be verified")

# A helper to print the result of a single PCI read
def print_a_pci_read (x, y, addr, val, comment=""):
    print(f"{x}-{y} 0x{addr:08x} => 0x{val:08x} ({val:d}) {comment}")

# Perform a burst of PCI reads and print results.
# If burst_type is 1, read the same location for a second and print a report
# If burst_type is 2, read an array of locations once and print a report
def print_a_pci_burst_read (device_id, x, y, noc_id, addr, burst_type = 1):
    if burst_type == 1:
        values = {}
        t_end = time.time() + 1
        print ("Sampling for 1 second...")
        while time.time() < t_end:
            val = tt_device.PCI_IFC.pci_read_xy(device_id, x, y, noc_id, addr)
            if val not in values:
                values[val] = 0
            values[val] += 1
        for val in values.keys():
            print_a_pci_read(x, y, addr, val, f"- {values[val]} times")
    elif burst_type >= 2:
        for k in range(0, burst_type):
            val = tt_device.PCI_IFC.pci_read_xy(device_id, x, y, noc_id, addr + 4*k)
            print_a_pci_read(x,y,addr + 4*k, val)

# Print all commands (help)
def print_available_commands (commands):
    rows = []
    for c in commands:
        desc = c['arguments_description'].split(':')
        row = [ f"{util.CLR_INFO}{c['short']}{util.CLR_END}", f"{util.CLR_INFO}{c['long']}{util.CLR_END}", f"{desc[0]}", f"{desc[1]}" ]
        rows.append(row)
    print (tabulate(rows, headers=[ "Short", "Long", "Arguments", "Description" ]))

# Certain commands give suggestions for next step. This function formats and prints those suggestions.
def print_navigation_suggestions (navigation_suggestions):
    if navigation_suggestions:
        print ("Speed dial:")
        rows = []
        for i in range (len(navigation_suggestions)):
            rows.append ([ f"{i}", f"{navigation_suggestions[i]['description']}", f"{navigation_suggestions[i]['cmd']}" ])
        print(tabulate(rows, headers=[ "#", "Description", "Command" ]))

# Test command (for development only)
def test_command(cmd, context, ui_state):
    return 0

# Main
def main(args, context):
    cmd_raw = ""

    # Create prompt object.
    prompt_session = PromptSession()

    # Init commands
    commands = [
        { "long" : "exit",
          "short" : "x",
          "expected_argument_count" : [ 0, 1 ],
          "arguments_description" : ": exit the program. If argument given, it will be used as the exit code"
        },
        { "long" : "help",
          "short" : "h",
          "expected_argument_count" : 0,
          "arguments_description" : ": prints command documentation"
        },
        { "long" : "epoch",
          "short" : "e",
          "expected_argument_count" : 1,
          "arguments_description" : "epoch_id : switch to epoch epoch_id"
        },
        { "long" : "buffer",
          "short" : "b",
          "expected_argument_count" : 1,
          "arguments_description" : "buffer_id : prints details on the buffer with ID buffer_id"
        },
        { "long" : "pipe",
          "short" : "p",
          "expected_argument_count" : 1,
          "arguments_description" : "pipe_id : prints details on the pipe with ID pipe_id"
        },
        {
          "long" : "pci-read-xy",
          "short" : "rxy",
          "expected_argument_count" : 3,
          "arguments_description" : "x y addr : read data from address 'addr' at noc0 location x-y of the chip associated with current epoch"
        },
        {
          "long" : "burst-read-xy",
          "short" : "brxy",
          "expected_argument_count" : 4,
          "arguments_description" : "x y addr burst_type : burst read data from address 'addr' at noc0 location x-y of the chip associated with current epoch. \nNCRISC status code address=0xffb2010c, BRISC status code address=0xffb3010c"
        },
        {
          "long" : "pci-write-xy",
          "short" : "wxy",
          "expected_argument_count" : 4,
          "arguments_description" : "x y addr value : writes value to address 'addr' at noc0 location x-y of the chip associated with current epoch"
        },

        {
          "long" : "dram-queue",
          "short" : "dq",
          "expected_argument_count" : 0,
          "arguments_description" : ": prints DRAM queue summary"
        },
        {
          "long" : "host-queue",
          "short" : "hq",
          "expected_argument_count" : 0,
          "arguments_description" : ": prints Host queue summary"
        },
        {
          "long" : "epoch-queue",
          "short" : "eq",
          "expected_argument_count" : 0,
          "arguments_description" : ": prints Epoch queue summary"
        },
        {
          "long" : "full-dump",
          "short" : "fd",
          "expected_argument_count" : 0,
          "arguments_description" : ": performs a full dump at current x-y"
        },
        {
          "long" : "test",
          "short" : "test",
          "expected_argument_count" : 0,
          "arguments_description" : ": test for development"
        }
    ]

    import_commands (commands)

    # Initialize current UI state
    ui_state = {
        "current_x": 1,           # Currently selected core (noc0 coordinates)
        "current_y": 1,
        "current_stream_id": 8,   # Currently selected stream_id
        "current_epoch_id": 0,    # Current epoch_id
        "current_graph_name": "", # Graph name for the current epoch
        "current_prompt": ""      # Based on the current x,y,stream_id tuple
    }

    navigation_suggestions = None

    def change_epoch (new_epoch_id):
        if context.netlist.epoch_id_to_graph_name(new_epoch_id) is not None:
            nonlocal ui_state
            ui_state["current_epoch_id"] = new_epoch_id
        else:
            print (f"{util.CLR_ERR}Invalid epoch id {new_epoch_id}{util.CLR_END}")

    # These commands will be executed right away (before allowing user input)
    non_interactive_commands=args.commands.split(";") if args.commands else []

    # Main command loop
    while True:
        have_non_interactive_commands=len(non_interactive_commands) > 0

        if ui_state['current_x'] is not None and ui_state['current_y'] is not None and ui_state['current_epoch_id'] is not None:
            row, col = tt_grayskull.noc0_to_rc (ui_state['current_x'], ui_state['current_y'])
            ui_state['current_prompt'] = f"core:{util.CLR_PROMPT}{ui_state['current_x']}-{ui_state['current_y']}{util.CLR_PROMPT_END} rc:{util.CLR_PROMPT}{row},{col}{util.CLR_PROMPT_END} stream:{util.CLR_PROMPT}{ui_state['current_stream_id']}{util.CLR_PROMPT_END} "

        try:
            ui_state['current_graph_name'] = context.netlist.epoch_id_to_graph_name(ui_state['current_epoch_id'])
            ui_state['current_device_id'] = context.netlist.graph_name_to_device_id(ui_state['current_graph_name'])
            ui_state['current_device'] = context.devices[ui_state['current_device_id']]

            print_navigation_suggestions (navigation_suggestions)

            if have_non_interactive_commands:
                cmd_raw = non_interactive_commands[0].strip()
                non_interactive_commands=non_interactive_commands[1:]
                if len(cmd_raw)>0:
                    print (f"{util.CLR_INFO}Executing command: %s{util.CLR_END}" % cmd_raw)
            else:
                my_prompt = f"Current epoch:{util.CLR_PROMPT}{ui_state['current_epoch_id']}{util.CLR_PROMPT_END}({ui_state['current_graph_name']}) device:{util.CLR_PROMPT}{ui_state['current_device_id']}{util.CLR_PROMPT_END} {ui_state['current_prompt']}> "
                cmd_raw = prompt_session.prompt(HTML(my_prompt))

            try: # To get a a command from the speed dial
                cmd_int = int(cmd_raw)
                cmd_raw = navigation_suggestions[cmd_int]["cmd"]
            except:
                pass

            cmd = cmd_raw.split ()
            if len(cmd) > 0:
                cmd_string = cmd[0]
                found_command = None

                # Look for command to execute
                for c in commands:
                    if c["short"] == cmd_string or c["long"] == cmd_string:
                        found_command = c
                        # Check arguments
                        if type(found_command["expected_argument_count"]) == list:
                            valid_arg_count_list = found_command["expected_argument_count"]
                        else:
                            valid_arg_count_list = [ found_command["expected_argument_count"] ]

                        if len(cmd)-1 not in valid_arg_count_list:
                            if len(valid_arg_count_list) == 1:
                                expected_args = valid_arg_count_list[0]
                                print (f"{util.CLR_ERR}Command '{found_command['long']}' requires {expected_args} argument{'s' if expected_args != 1 else ''}: {found_command['arguments_description']}{util.CLR_END}")
                            else:
                                print (f"{util.CLR_ERR}Command '{found_command['long']}' requires one of {valid_arg_count_list} arguments: {found_command['arguments_description']}{util.CLR_END}")
                            found_command = 'invalid-args'
                        break

                if found_command == None:
                    # Print help on invalid commands
                    print (f"{util.CLR_ERR}Invalid command '{cmd_string}'{util.CLR_END}\nAvailable commands:")
                    print_available_commands (commands)
                elif found_command == 'invalid-args':
                    # This was handled earlier
                    pass
                else:
                    if found_command["long"] == "exit":
                        exit_code = int(cmd[1]) if len(cmd) > 1 else 0
                        return exit_code
                    elif found_command["long"] == "help":
                        print_available_commands (commands)
                    elif found_command["long"] == "test":
                        test_command (cmd, context, ui_state)
                    elif found_command["long"] == "epoch":
                        change_epoch (int(cmd[1]))
                    elif found_command["long"] == "buffer":
                        navigation_suggestions = print_buffer_data (cmd, context)
                    elif found_command["long"] == "pipe":
                        navigation_suggestions = print_pipe_data (cmd, context)
                    elif found_command["long"] == "pci-read-xy" or found_command["long"] == "burst-read-xy" or found_command["long"] == "pci-write-xy":
                        x = int(cmd[1],0)
                        y = int(cmd[2],0)
                        addr = int(cmd[3],0)
                        if found_command["long"] == "pci-read-xy":
                            data = tt_device.PCI_IFC.pci_read_xy (ui_state['current_device_id'], x, y, 0, addr)
                            print_a_pci_read (x, y, addr, data)
                        elif found_command["long"] == "burst-read-xy":
                            burst_type = int(cmd[4],0)
                            print_a_pci_burst_read (ui_state['current_device_id'], x, y, 0, addr, burst_type=burst_type)
                        elif found_command["long"] == "pci-write-xy":
                            tt_device.PCI_IFC.pci_write_xy (ui_state['current_device_id'], x, y, 0, addr, data = int(cmd[4],0))
                        else:
                            print (f"{util.CLR_ERR} Unknown {found_command['long']} {util.CLR_END}")
                    elif found_command["long"] == "full-dump":
                        ui_state['current_device'].full_dump_xy(ui_state['current_x'], ui_state['current_y'])
                    elif found_command["long"] == "dram-queue":
                        print_dram_queue_summary (cmd, context, ui_state)
                    elif found_command["long"] == "host-queue":
                        print_host_queue_summary (cmd, context, ui_state)
                    elif found_command["long"] == "epoch-queue":
                        print_epoch_queue_summary(cmd, context, ui_state)
                    else:
                        navigation_suggestions = found_command["module"].run(cmd, context, ui_state)

        except Exception as e:
            print (f"Exception: {util.CLR_ERR} {e} {util.CLR_END}")
            print(traceback.format_exc())
            if have_non_interactive_commands:
                raise
            else:
                raise
    return 0

# Import any 'plugin' commands from debuda-commands directory
def import_commands (command_metadata_array):
    command_files = []
    for root, dirnames, filenames in os.walk(util.application_path () + '/debuda-commands'):
        for filename in fnmatch.filter(filenames, '*.py'):
            command_files.append(os.path.join(root, filename))

    sys.path.append(util.application_path() + '/debuda-commands')

    for cmdfile in command_files:
        module_path = os.path.splitext(os.path.basename(cmdfile))[0]
        my_cmd_module = importlib.import_module (module_path)
        command_metadata = my_cmd_module.command_metadata
        command_metadata["module"] = my_cmd_module
        command_metadata["long"] = my_cmd_module.__name__
        util.VERBOSE (f"Importing command '{my_cmd_module.__name__}'")

        # Check command names/shortcuts
        for cmd in command_metadata_array:
            if cmd["long"] == command_metadata["long"]:
                util.FATAL (f"Command {cmd['long']} already exists")
            if cmd["short"] == command_metadata["short"]:
                util.FATAL (f"Commands {cmd['long']} and {command_metadata['long']} use the same shortcut: {cmd['short']}")

        command_metadata_array.append (command_metadata)

# Initialize communication with the client (debuda-stub)
tt_device.init_comm_client (args.debug_debuda_stub)

# Make sure to terminate communication client (debuda-stub) on exit
atexit.register (tt_device.terminate_comm_client_callback)

# Handle server cache
tt_device.DEBUDA_SERVER_CACHED_IFC.enabled = args.server_cache == "through" or args.server_cache == "on"
tt_device.DEBUDA_SERVER_IFC.enabled = args.server_cache == "through" or args.server_cache == "off"
if tt_device.DEBUDA_SERVER_CACHED_IFC.enabled:
    atexit.register (tt_device.DEBUDA_SERVER_CACHED_IFC.save)
    tt_device.DEBUDA_SERVER_CACHED_IFC.load()

# Create context
if args.output_dir is None: # Then find the most recent tt_build subdir
    most_recent_modification_time = None
    for tt_build_subfile in os.listdir("tt_build"):
        subdir = f"tt_build/{tt_build_subfile}"
        if os.path.isdir(subdir):
            if most_recent_modification_time is None or os.path.getmtime(subdir) > most_recent_modification_time:
                most_recent_modification_time = os.path.getmtime(subdir)
                most_recent_subdir = subdir
    print (most_recent_subdir)
    args.output_dir = most_recent_subdir
    util.INFO (f"Output directory not specified: looking for the most recent tt_build/ subdirectory. Found: {most_recent_subdir}")

context = tt_netlist.load (netlist_filepath = args.netlist, run_dirpath = args.output_dir)

# Initialize context
context.stream_cache_enabled = args.stream_cache

# Main function
exit_code = main(args, context)
util.INFO (f"Exiting with code {exit_code} ")
sys.exit (exit_code)
