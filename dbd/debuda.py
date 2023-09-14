#!/usr/bin/env python3
"""
Debuda parses the build output files and probes the silicon to determine the status of a Buda run.
Main help: http://yyz-webservice-02.local.tenstorrent.com/docs/debuda-docs/debuda_py

"""
try:
    from multiprocessing.dummy import Array
    import sys, os, argparse, traceback, fnmatch, importlib
    from tabulate import tabulate
    import tt_util as util, tt_device, tt_netlist
    from prompt_toolkit import PromptSession
    from prompt_toolkit.formatted_text import HTML
except ModuleNotFoundError as e:
    # Print the exception and call stack
    traceback.print_exc()

    # ANSI escape sequence for red text
    red_start = "\033[31m"
    red_end = "\033[0m"

    # Print custom message in red
    print(f"Try: {red_start}pip install sortedcontainers prompt_toolkit pyzmq tabulate rapidyaml deprecation docopt; make dbd{red_end}")
    exit(1)
from tt_coordinate import OnChipCoordinate

# Argument parsing
def get_argument_parser ():
    parser = argparse.ArgumentParser(description=__doc__ + tt_device.STUB_HELP)
    parser.add_argument('output_dir', type=str, nargs='?', default=None, help='Output directory of a buda run. If left blank, the most recent subdirectory of tt_build/ will be used, and the netlist file will be inferred from the runtime_data.yaml file found there.')
    parser.add_argument('--netlist',  type=str, required=False, default=None, help='Netlist file to import. If not supplied, the most recent subdirectory of tt_build/ will be used.')
    parser.add_argument('--commands', type=str, required=False, help='Execute a list of semicolon-separated commands.')
    parser.add_argument('--server-cache', type=str, default='off', help=f'Specifies the method of communication with the Debuda Server. When "off" (default), all device reads are done through the server (silicon). When set to "through", an attempt to read from the cache will be made at first; if the cache does not contain the data, the server will be queried. When "on", all reads are from cache only; a non-existent cache entry will result in an error.')
    parser.add_argument('--verbose', action='store_true', default=False, help=f'Print verbose output.')
    parser.add_argument('--test', action='store_true', default=False, help=f'Exits with non-zero exit code on any exception.')
    parser.add_argument('--debuda-server-address', type=str, default="localhost:5555", required=False, help='IP address of debuda server (e.g. remote.server.com:5555). By default, the server is assumed to be running on the local machine.')
    return parser

# Creates rows for tabulate for all commands of a given type
def format_commands (commands, type):
    rows = []
    for c in commands:
        if c['type'] == type:
            description = c['description']
            row = [ f"{util.CLR_INFO}{c['long']}{util.CLR_END}", f"{c['short']}", f"{description}" ]
            rows.append(row)
    return rows

# Print all commands (help)
def print_help (commands):
    rows = []
    rows += format_commands (commands, 'housekeeping')
    rows += format_commands (commands, 'low-level')
    rows += format_commands (commands, 'high-level')
    print (tabulate(rows, headers=["Long Form", "Short", "Description"]))
    # format_commands (commands, 'dev', "Development")

# Certain commands give suggestions for next step. This function formats and prints those suggestions.
def print_navigation_suggestions (navigation_suggestions):
    if navigation_suggestions:
        print ("Speed dial:")
        rows = []
        for i in range (len(navigation_suggestions)):
            rows.append ([ f"{i}", f"{navigation_suggestions[i]['description']}", f"{navigation_suggestions[i]['cmd']}" ])
        print(tabulate(rows, headers=[ "#", "Description", "Command" ]))

# Imports 'plugin' commands from debuda_commands/ directory
# With 'reload' argument set to True, the debuda_commands can be live-reloaded (using importlib.reload)
def import_commands (reload = False):
    # Built-in commands
    commands = [
        { "long" : "exit",
          "short" : "x",
          "type" : "housekeeping",
          "expected_argument_count" : [ 0, 1 ],
          "arguments" : "exit_code",
          "description" : "Exits the program. The optional argument represents the exit code. Defaults to 0."
        },
        { "long" : "help",
          "short" : "h",
          "type" : "housekeeping",
          "expected_argument_count" : [ 0 ],
          "arguments" : "",
          "description" : "Prints documentation summary."
        },
        { "long" : "reload",
          "short" : "rl",
          "type" : "dev",
          "expected_argument_count" : [ 0 ],
          "arguments" : "",
          "description" : "Reloads files in debuda_commands directory."
        },
    ]

    cmd_files = []
    for root, dirnames, filenames in os.walk(util.application_path () + '/debuda_commands'):
        for filename in fnmatch.filter(filenames, '*.py'):
            cmd_files.append(os.path.join(root, filename))

    sys.path.append(util.application_path() + '/debuda_commands')

    cmd_files.sort()
    for cmdfile in cmd_files:
        module_path = os.path.splitext(os.path.basename(cmdfile))[0]
        try:
            cmd_module = importlib.import_module (module_path)
        except Exception as e:
            if "lineno" in e.__dict__:
                util.ERROR (f"Error in file {cmdfile}:{e.lineno}: {e.msg}")
            else:
                util.ERROR (f"Error in file {cmdfile}: {e}")
            continue
        command_metadata = cmd_module.command_metadata
        command_metadata["module"] = cmd_module

        # Make the module name the default 'long' invocation string
        if "long" not in command_metadata:
            command_metadata["long"] = cmd_module.__name__
        util.VERBOSE (f"Importing command {command_metadata['long']} from '{cmd_module.__name__}'")

        if reload:
            importlib.reload(cmd_module)

        # Check command names/shortcut overlap (only when not reloading)
        for cmd in commands:
            if cmd["long"] == command_metadata["long"]:
                util.FATAL (f"Command {cmd['long']} already exists")
            if cmd["short"] == command_metadata["short"]:
                util.FATAL (f"Commands {cmd['long']} and {command_metadata['long']} use the same shortcut: {cmd['short']}")
        commands.append (command_metadata)
    return commands

# Finds the most recent build directory
def locate_most_recent_build_output_dir ():
    # Try to find a default output directory
    most_recent_modification_time = None
    try:
        for tt_build_subfile in os.listdir("tt_build"):
            subdir = f"tt_build/{tt_build_subfile}"
            if os.path.isdir(subdir):
                if most_recent_modification_time is None or os.path.getmtime(subdir) > most_recent_modification_time:
                    most_recent_modification_time = os.path.getmtime(subdir)
                    most_recent_subdir = subdir
        return most_recent_subdir
    except:
        pass
    return None

# Loads all files necessary to debug a single buda run
# Returns a debug 'context' that contains the loaded information
def load_context (netlist_filepath, run_dirpath, runtime_data_yaml, cluster_desc_path):
    # All-encompassing structure representing a Debuda context
    class Context:
        netlist = None      # Netlist and related 'static' data (i.e. data stored in files such as blob.yaml, pipegen.yaml)
        devices = None      # A list of objects of class Device used to obtain 'dynamic' data (i.e. data read from the devices)
        cluster_desc = None # Cluster description (i.e. the 'cluster_desc.yaml' file)
        def __repr__(self):
            return f"context"

    util.VERBOSE (f"Initializing context")
    context = Context()

    # Load netlist files
    context.netlist = tt_netlist.Netlist(netlist_filepath, run_dirpath, runtime_data_yaml)

    # Load the cluster descriptor. This file is created by the tt_runtime::tt_runtime -> generate_cluster_descriptor.
    # There is also a 'cluster_desc.yaml' file in the run_dirpath directory...
    if not os.path.exists(cluster_desc_path):
        util.FATAL (f"Cluster descriptor file '{cluster_desc_path}' does not exist. Exiting...")
    else:
        context.cluster_desc = util.YamlFile(cluster_desc_path)

    # Create the devices
    arch = context.netlist.get_arch ()
    device_ids = context.netlist.get_device_ids()
    context.devices = dict()
    for device_id in device_ids:
        device_desc_path = tt_device.get_soc_desc_path(device_id, run_dirpath)
        # util.INFO(f"Loading device {device_id} from {device_desc_path}")
        context.devices[device_id] = tt_device.Device.create(arch, device_id=device_id, cluster_desc=context.cluster_desc.root, device_desc_path=device_desc_path)

    return context

# Main
def main(args, context):
    cmd_raw = ""

    # Create prompt object.
    context.prompt_session = PromptSession()

    commands = import_commands ()
    current_device = context.devices[0]

    # Initialize current UI state
    ui_state = {
        "current_loc"       : OnChipCoordinate(0, 0, "netlist", current_device), # Currently selected core
        "current_stream_id" : 8,                                                 # Currently selected stream_id
        "current_graph_name": context.netlist.graphs.first().id(),               # Currently selected graph name
        "current_prompt"    : "",                                                # Based on the current x,y,stream_id tuple
        "current_device"    : current_device,                                    # Currently selected device
        "current_device_id" : 0,                                                 # Currently selected device id
    }

    navigation_suggestions = None

    # These commands will be executed right away (before allowing user input)
    non_interactive_commands=args.commands.split(";") if args.commands else []

    # Main command loop
    while True:
        have_non_interactive_commands=len(non_interactive_commands) > 0
        current_loc = ui_state['current_loc']

        if ui_state['current_loc'] is not None and ui_state['current_graph_name'] is not None and ui_state['current_device'] is not None:
            ui_state['current_prompt'] = f"NocTr:{util.CLR_PROMPT}{current_loc.to_str()}{util.CLR_PROMPT_END} "
            ui_state['current_prompt'] += f"netlist:{util.CLR_PROMPT}{current_loc.to_str('netlist')}{util.CLR_PROMPT_END} "
            ui_state['current_prompt'] += f"stream:{util.CLR_PROMPT}{ui_state['current_stream_id']}{util.CLR_PROMPT_END} "
            graph = context.netlist.graph(ui_state['current_graph_name'])
            op_name = graph.location_to_op_name(current_loc)
            ui_state['current_prompt'] += f"op:{util.CLR_PROMPT}{op_name}{util.CLR_PROMPT_END} "


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
                cmd_raw = context.prompt_session.prompt(HTML(my_prompt))

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

                if found_command == None:
                    # Print help on invalid commands
                    print_help (commands)
                    raise util.TTException (f"Invalid command '{cmd_string}'")
                else:
                    if found_command["long"] == "exit":
                        exit_code = int(cmd[1]) if len(cmd) > 1 else 0
                        return exit_code
                    elif found_command["long"] == "help":
                        print_help (commands)
                    elif found_command["long"] == "reload":
                        import_commands (reload=True)
                    else:
                        new_navigation_suggestions = found_command["module"].run(cmd_raw, context, ui_state)
                        if new_navigation_suggestions:
                            navigation_suggestions = new_navigation_suggestions

        except Exception as e:
            if args.test: # Always raise in test mode
                raise
            if have_non_interactive_commands or type(e) == util.TTFatalException:
                # In non-interactive mode and on fatal excepions, we re-raise to exit the program
                raise
            else:
                # Otherwise, we print the call stack, but continue the REPL
                util.notify_exception (type(e), e, e.__traceback__)
        except SystemExit as e:
            print (e)

    return 0

if __name__ == '__main__':
    parser=get_argument_parser()
    args = parser.parse_args()

    if not args.verbose:
        util.VERBOSE=util.NULL_PRINT

    # Try to determine the output directory
    if args.output_dir is None: # Then try to find the most recent tt_build subdir
        most_recent_build_output_dir = locate_most_recent_build_output_dir()
        if most_recent_build_output_dir:
            util.INFO (f"Output directory not specified. Using most recently changed subdirectory of tt_build: {os.getcwd()}/{most_recent_build_output_dir}")
            args.output_dir = most_recent_build_output_dir
        else:
            util.FATAL (f"Output directory (output_dir) was not supplied and cannot be determined automatically. Exiting...")

    # Try to load the runtime data from the output directory
    runtime_data_yaml_filename = f"{(args.output_dir)}/runtime_data.yaml"
    runtime_data_yaml = None
    if os.path.exists(runtime_data_yaml_filename):
        runtime_data_yaml = util.YamlFile(runtime_data_yaml_filename)

    # Try to connect to the server. If it is not already running, it will be started.
    server_ifc = tt_device.init_server_communication(args, runtime_data_yaml_filename)

    # We did not find the runtime_data.yaml file, so we need to get the runtime data from the server
    if runtime_data_yaml is None:
        runtime_data_yaml = server_ifc.get_runtime_data()

    cluster_desc_path = os.path.abspath (server_ifc.get_cluster_desc_path())

    # Create the context
    context = load_context (netlist_filepath = args.netlist, run_dirpath=args.output_dir, runtime_data_yaml=runtime_data_yaml, cluster_desc_path=cluster_desc_path)
    context.server_ifc = server_ifc
    context.args = args             # Used by 'export' command
    context.debuda_path = __file__  # Used by 'export' command

    # If we spawned the Debuda server, the runtime_data provided by debuda server is not valid, and we use the runtime_data.yaml file saved by the run
    # As the server_ifc might get probed for the data, we set the get_runtime_data function to return the runtime_data_yaml
    if server_ifc.spawning_debuda_stub:
        server_ifc.get_runtime_data = lambda: context.netlist.runtime_data_yaml

    # Main function
    exit_code = main(args, context)

    util.VERBOSE (f"Exiting with code {exit_code} ")
    sys.exit (exit_code)
