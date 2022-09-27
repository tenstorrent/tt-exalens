#!/usr/bin/env python3
"""
debuda parses the build output files and probes the silicon to determine status of a buda run.
"""
import sys, os, argparse, time, traceback, fnmatch, importlib, zipfile
from tabulate import tabulate
from tt_object import DataArray
import tt_util as util, tt_device, tt_netlist
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from tt_graph import Queue

parser = argparse.ArgumentParser(description=__doc__ + tt_device.STUB_HELP)
parser.add_argument('output_dir', type=str, nargs='?', default=None, help='Output directory of a buda run. If left blank, the most recent subdirectory of tt_build/ will be used')
parser.add_argument('--netlist',  type=str, required=False, default=None, help='Netlist file to import. If not supplied, the most recent subdirectory of tt_build/ will be used')
parser.add_argument('--commands', type=str, required=False, help='Execute a set of commands separated by ;')
parser.add_argument('--server-cache', type=str, default='off', help=f'Directs communication with Debuda Server. When "off", all device reads are done through the server. When set to "through", attempt to read from cache first. When "on", all reads are from cache only.')
parser.add_argument('--debug-debuda-stub', action='store_true', default=False, help=f'Prints all transactions on PCIe. Also, starts debuda-stub with --debug to print transfers.')
parser.add_argument('--verbose', action='store_true', default=False, help=f'Prints additional information.')
parser.add_argument('--debuda-server-address', type=str, default="localhost:5555", required=False, help='IP address of debuda server (e.g. remote.server.com:5555);')
args = parser.parse_args()
util.args = args

### BUILT-IN COMMANDS

# A helper to print the result of a single PCI read
def print_a_pci_read (x, y, addr, val, comment=""):
    print(f"{util.noc_loc_str((x, y))} 0x{addr:08x} => 0x{val:08x} ({val:d}) {comment}")

# A helper function to parse print_format
def get_print_format(print_format):
    is_hex_bytes_per_entry_dict = {
        "i32"  :[False, 4],
        "i16"  :[False,2],
        "i8"   :[False,1],
        "hex32":[True, 4],
        "hex16":[True,2],
        "hex8" :[True,1]}
    return is_hex_bytes_per_entry_dict[print_format]
# Perform a burst of PCI reads and print results.
# If burst_type is 1, read the same location for a second and print a report
# If burst_type is 2, read an array of locations once and print a report
def print_a_pci_burst_read (device_id, x, y, noc_id, addr, burst_type = 1, print_format = "hex32"):
    if burst_type == 1:
        values = {}
        t_end = time.time() + 1
        print ("Sampling for 1 second...")
        while time.time() < t_end:
            val = tt_device.SERVER_IFC.pci_read_xy(device_id, x, y, noc_id, addr)
            if val not in values:
                values[val] = 0
            values[val] += 1
        for val in values.keys():
            print_a_pci_read(x, y, addr, val, f"- {values[val]} times")
    elif burst_type >= 2:
        num_words = burst_type
        da = DataArray(f"L1-0x{addr:08x}-{num_words * 4}", 4)
        for i in range (num_words):
            data = tt_device.SERVER_IFC.pci_read_xy(device_id, x, y, noc_id, addr + 4*i)
            da.data.append(data)
        is_hex, bytes_per_entry = get_print_format(print_format)
        if bytes_per_entry != 4:
            da.to_bytes_per_entry(bytes_per_entry)
        formated = f"{da._id}\n" + util.dump_memory(addr, da.data, bytes_per_entry, 16, is_hex)
        print(formated)

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
          "arguments_description" : ": exits the program. If an argument is supplied, it will be used as the exit code"
        },
        { "long" : "help",
          "short" : "h",
          "expected_argument_count" : 0,
          "arguments_description" : ": prints command documentation"
        },
        { "long" : "reload",
          "short" : "rl",
          "expected_argument_count" : 0,
          "arguments_description" : ": reloads files in debuda-commands directory"
        },
        { "long" : "export",
          "short" : "xp",
          "expected_argument_count" : [ 0, 1 ],
          "arguments_description" : f"[ filename ]: exports a zip package for offline work. The optional argument represents a zip file name. Defaults to '{ util.DEFAULT_EXPORT_FILENAME }'"
        },
        { "long" : "epoch",
          "short" : "e",
          "expected_argument_count" : 1,
          "arguments_description" : "epoch_id : [DEPRECATED - use 'graph' instead]"
        },
        { "long" : "graph",
          "short" : "g",
          "expected_argument_count" : 1,
          "arguments_description" : "graph_name : switch to graph graph_name"
        },
        {
          "long" : "pci-read-xy",
          "short" : "rxy",
          "expected_argument_count" : 3,
          "arguments_description" : "x y addr : read data from address 'addr' at noc0 location x-y of the chip associated with current epoch"
        },
        {
          "long" : "pci-raw-read",
          "short" : "pcir",
          "expected_argument_count" : 1,
          "arguments_description" : "addr : read data from PCI bar at address 'addr"
        },
        {
          "long" : "pci-raw-write",
          "short" : "pciw",
          "expected_argument_count" : 2,
          "arguments_description" : "addr data: write 'data' to PCI bar at address 'addr"
        },
        {
          "long" : "burst-read-xy",
          "short" : "brxy",
          "expected_argument_count" : [4,5],
          "arguments_description" : "x y addr burst_type print_format: burst read data from address 'addr' at noc0 location x-y of the chip associated with current epoch. \nNCRISC status code address=0xffb2010c, BRISC status code address=0xffb3010c\nPrint formats i8, i16, i32, hex8, hex16, hex32"
        },
        {
          "long" : "pci-write-xy",
          "short" : "wxy",
          "expected_argument_count" : 4,
          "arguments_description" : "x y addr value : writes value to address 'addr' at noc0 location x-y of the chip associated with current epoch"
        },
    ]

    import_commands (commands)

    # Initialize current UI state
    ui_state = {
        "current_x": 1,             # Currently selected core (noc0 coordinates)
        "current_y": 1,
        "current_stream_id": 8,     # Currently selected stream_id
        "current_graph_name": context.netlist.graphs.first().id(), # Currently selected graph name
        "current_prompt": "",       # Based on the current x,y,stream_id tuple
        "current_device": None
    }

    navigation_suggestions = None

    # These commands will be executed right away (before allowing user input)
    non_interactive_commands=args.commands.split(";") if args.commands else []

    # Main command loop
    while True:
        have_non_interactive_commands=len(non_interactive_commands) > 0
        noc0_loc = ( ui_state['current_x'], ui_state['current_y'] )

        if ui_state['current_x'] is not None and ui_state['current_y'] is not None and ui_state['current_graph_name'] is not None and ui_state['current_device'] is not None:
            row, col = ui_state['current_device'].noc0_to_rc ( noc0_loc )
            ui_state['current_prompt'] = f"core:{util.CLR_PROMPT}{util.noc_loc_str(noc0_loc)}{util.CLR_PROMPT_END} rc:{util.CLR_PROMPT}{row},{col}{util.CLR_PROMPT_END} stream:{util.CLR_PROMPT}{ui_state['current_stream_id']}{util.CLR_PROMPT_END} "

        try:
            ui_state['current_device_id'] = context.netlist.graph_name_to_device_id(ui_state['current_graph_name'])
            ui_state['current_device'] = context.devices[ui_state['current_device_id']] if ui_state['current_device_id'] is not None else None

            print_navigation_suggestions (navigation_suggestions)

            if have_non_interactive_commands:
                cmd_raw = non_interactive_commands[0].strip()
                non_interactive_commands=non_interactive_commands[1:]
                if len(cmd_raw)>0:
                    print (f"{util.CLR_INFO}Executing command: %s{util.CLR_END}" % cmd_raw)
            else:
                my_prompt = f"Current epoch:{util.CLR_PROMPT}{context.netlist.graph_name_to_epoch_id(ui_state['current_graph_name'])}{util.CLR_PROMPT_END}({ui_state['current_graph_name']}) device:{util.CLR_PROMPT}{ui_state['current_device_id']}{util.CLR_PROMPT_END} {ui_state['current_prompt']}> "
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
                    elif found_command["long"] == "reload":
                        import_commands (commands, reload=True)
                    elif found_command["long"] == "export":
                        zip_file_name = cmd[1] if len(cmd) > 1 else util.DEFAULT_EXPORT_FILENAME

                        # 1. Add all Yaml files
                        filelist = [ f for f in util.YamlFile.file_cache ]

                        # 2. See if server cache is made
                        if tt_device.DEBUDA_SERVER_CACHED_IFC.enabled:
                            tt_device.DEBUDA_SERVER_CACHED_IFC.save()
                            filelist.append (tt_device.DEBUDA_SERVER_CACHED_IFC.filepath)
                        else:
                            util.WARN ("Warning: server cache is missing and will not be exported (see '--server-cache')")

                        # 3. Save command history
                        COMMAND_HISTORY_FILENAME="debuda-command-history.yaml"
                        util.write_to_yaml_file (prompt_session.history.get_strings(), COMMAND_HISTORY_FILENAME)
                        filelist.append (COMMAND_HISTORY_FILENAME)

                        if util.export_to_zip (filelist, out_file=zip_file_name):
                            print (f"{util.CLR_GREEN}Exported '{zip_file_name}'. Import with:\n  unzip {zip_file_name} -d dbd-export\n  cd dbd-export\n  Run debuda.py {'--server-cache on' if tt_device.DEBUDA_SERVER_CACHED_IFC.enabled else ''}{util.CLR_END}")
                    elif found_command["long"] == "graph":
                        gname = cmd[1]
                        if gname not in context.netlist.graph_names():
                            util.WARN (f"Invalid graph {gname}. Available graphs: {', '.join (list(context.netlist.graph_names()))}")
                        else:
                            ui_state["current_graph_name"] = cmd[1]
                    elif found_command["long"] == "epoch":
                        util.WARN ("'epoch' command is deprecated: use 'graph' command instead")
                    elif found_command["long"] == "pci-raw-read":
                        addr = int(cmd[1],0)
                        print ("PCI RD [0x%x]: 0x%x" % (addr, tt_device.SERVER_IFC.pci_raw_read (ui_state['current_device_id'], addr)))
                    elif found_command["long"] == "pci-raw-write":
                        addr = int(cmd[1],0)
                        data = int(cmd[2],0)
                        print ("PCI WR [0x%x] <- 0x%x" % (addr, tt_device.SERVER_IFC.pci_raw_write (ui_state['current_device_id'], addr, data)))
                    elif found_command["long"] == "pci-read-xy" or found_command["long"] == "burst-read-xy" or found_command["long"] == "pci-write-xy":
                        x = int(cmd[1],0)
                        y = int(cmd[2],0)
                        addr = int(cmd[3],0)
                        if found_command["long"] == "pci-read-xy":
                            data = tt_device.SERVER_IFC.pci_read_xy (ui_state['current_device_id'], x, y, 0, addr)
                            print_a_pci_read (x, y, addr, data)
                        elif found_command["long"] == "burst-read-xy":
                            burst_type = int(cmd[4],0)
                            print_format = "hex32"
                            if (len(cmd) > 5):
                                print_format = cmd[5]
                            print_a_pci_burst_read (ui_state['current_device_id'], x, y, 0, addr, burst_type=burst_type, print_format=print_format)
                        elif found_command["long"] == "pci-write-xy":
                            tt_device.SERVER_IFC.pci_write_xy (ui_state['current_device_id'], x, y, 0, addr, data = int(cmd[4],0))
                        else:
                            print (f"{util.CLR_ERR} Unknown {found_command['long']} {util.CLR_END}")
                    else:
                        navigation_suggestions = found_command["module"].run(cmd, context, ui_state)

        except Exception as e:
            if have_non_interactive_commands:
                raise
            else:
                util.notify_exception (type(e), e, e.__traceback__) # Print the exception
    return 0

# Import 'plugin' commands from debuda-commands directory
# With reload=True, the debuda-commands can be live-reloaded (importlib.reload)
def import_commands (command_metadata_array, reload = False):
    cmd_files = []
    for root, dirnames, filenames in os.walk(util.application_path () + '/debuda-commands'):
        for filename in fnmatch.filter(filenames, '*.py'):
            cmd_files.append(os.path.join(root, filename))

    sys.path.append(util.application_path() + '/debuda-commands')

    cmd_files.sort()
    for cmdfile in cmd_files:
        module_path = os.path.splitext(os.path.basename(cmdfile))[0]
        try:
            cmd_module = importlib.import_module (module_path)
        except Exception as e:
            util.ERROR (f"Error in module {module_path}: {e}")
            continue
        command_metadata = cmd_module.command_metadata
        command_metadata["module"] = cmd_module

        # Make the module name the default 'long' invocation string
        if "long" not in command_metadata:
            command_metadata["long"] = cmd_module.__name__
        util.VERBOSE (f"Importing command '{cmd_module.__name__}'")

        if reload:
            for i, c in enumerate(command_metadata_array):
                if c["long"] == command_metadata["long"]:
                    command_metadata_array[i] = command_metadata
                    importlib.reload(cmd_module)
        else:
            # Check command names/shortcut overlap (only when not reloading)
            for cmd in command_metadata_array:
                if cmd["long"] == command_metadata["long"]:
                    util.FATAL (f"Command {cmd['long']} already exists")
                if cmd["short"] == command_metadata["short"]:
                    util.FATAL (f"Commands {cmd['long']} and {command_metadata['long']} use the same shortcut: {cmd['short']}")
            command_metadata_array.append (command_metadata)

def locate_output_dir ():
    # Try to find a default output directory
    most_recent_modification_time = None
    try:
        for tt_build_subfile in os.listdir("tt_build"):
            subdir = f"tt_build/{tt_build_subfile}"
            if os.path.isdir(subdir):
                if most_recent_modification_time is None or os.path.getmtime(subdir) > most_recent_modification_time:
                    most_recent_modification_time = os.path.getmtime(subdir)
                    most_recent_subdir = subdir
        util.INFO (f"Output directory not specified. Using most recently changed subdirectory of tt_build: {os.getcwd()}/{most_recent_subdir}")
        return most_recent_subdir
    except:
        pass
    return None

# Loads all files necessary to debug a single buda run
# Returns a debug 'context' that contains the loaded information
def load_context (netlist_filepath, run_dirpath):
    # All-encompassing structure representing a Debuda context
    class Context:
        netlist = None      # Netlist and related 'static' data (i.e. data stored in files such as blob.yaml, pipegen.yaml)
        devices = None      # A list of objects of class Device used to obtain 'dynamic' data (i.e. data read from the devices)
        pass

    util.VERBOSE (f"Initializing context")
    context = Context()

    # Load netlist files
    context.netlist = tt_netlist.Netlist(netlist_filepath, run_dirpath)

    # Create the devices
    arch = context.netlist.get_arch ()
    device_ids = context.netlist.get_device_ids()
    context.devices = { i : tt_device.Device.create(arch) for i in device_ids }

    return context

### START

if args.output_dir is None: # Then find the most recent tt_build subdir
    args.output_dir = locate_output_dir()

if args.output_dir is None:
    util.FATAL (f"Output directory (output_dir) was not supplied and cannot be determined automatically. Exiting...")

# Try to connect to the server
server_ifc = tt_device.init_server_communication(args)
runtime_data = server_ifc.get_runtime_data()

# Create the context
context = load_context (netlist_filepath = args.netlist, run_dirpath=args.output_dir)
args.path_to_runtime_yaml = context.netlist.runtime_data_yaml.filepath
context.server_ifc = server_ifc

# Main function
exit_code = main(args, context)

util.INFO (f"Exiting with code {exit_code} ")
sys.exit (exit_code)
