#!/usr/bin/env python3
"""
debuda parses the build output files and probes the silicon to determine status of a buda run.
"""
from multiprocessing.dummy import Array
import sys, os, argparse, time, traceback, fnmatch, importlib, zipfile
from tabulate import tabulate
from tt_object import DataArray
import tt_util as util, tt_device, tt_netlist
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from tt_graph import Queue

def get_parser ():
    parser = argparse.ArgumentParser(description=__doc__ + tt_device.STUB_HELP)
    parser.add_argument('output_dir', type=str, nargs='?', default=None, help='Output directory of a buda run. If left blank, the most recent subdirectory of tt_build/ will be used, and the netlist file will be inferred from the runtime_data.yaml file.')
    parser.add_argument('--netlist',  type=str, required=False, default=None, help='Netlist file to import. If not supplied, the most recent subdirectory of tt_build/ will be used.')
    parser.add_argument('--commands', type=str, required=False, help='Execute a list commands (semicolon-separated).')
    parser.add_argument('--server-cache', type=str, default='off', help=f'Directs communication with Debuda Server. When "off", all device reads are done through the server. When set to "through", attempt to read from cache first. When "on", all reads are from cache only.')
    parser.add_argument('--verbose', action='store_true', default=False, help=f'Prints additional information.')
    parser.add_argument('--debuda-server-address', type=str, default="localhost:5555", required=False, help='IP address of debuda server (e.g. remote.server.com:5555).')
    return parser

# Creates rows for tabulate for all commands of a given type
def format_commands (commands, type):
    rows = []
    for c in commands:
        if c['type'] == type:
            arguments = c['arguments']
            description = c['description']
            eac = c['expected_argument_count']
            expected_argument_count = "/".join ([ str(a) for a in eac ])
            row = [ f"{util.CLR_INFO}{c['long']}{util.CLR_END}", f"{c['short']}", f"{expected_argument_count}", f"{arguments}", f"{description}" ]
            rows.append(row)
    return rows

# Print all commands (help)
def print_help (commands):
    rows = []
    rows += format_commands (commands, 'housekeeping')
    rows += format_commands (commands, 'low-level')
    rows += format_commands (commands, 'high-level')
    print (tabulate(rows, headers=["Long Form", "Short", "Arg count", "Arguments", "Description"]))
    # format_commands (commands, 'dev', "Development")

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
    context.prompt_session = PromptSession()

    commands = import_commands ()

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
                        # Check arguments
                        valid_arg_count_list = found_command["expected_argument_count"]

                        if len(cmd)-1 not in valid_arg_count_list:
                            if len(valid_arg_count_list) == 1:
                                expected_args = valid_arg_count_list[0]
                                print (f"{util.CLR_ERR}Command '{found_command['long']}' requires {expected_args} argument{'s' if expected_args != 1 else ''}: {found_command['arguments']}")
                            else:
                                print (f"{util.CLR_ERR}Command '{found_command['long']}' requires one of {valid_arg_count_list} arguments: {found_command['arguments']}")
                            found_command = 'invalid-args'
                        break

                if found_command == None:
                    # Print help on invalid commands
                    print (f"{util.CLR_ERR}Invalid command '{cmd_string}'{util.CLR_END}\nAvailable commands:")
                    print_help (commands)

                elif found_command == 'invalid-args':
                    # This was handled earlier
                    pass
                else:
                    if found_command["long"] == "exit":
                        exit_code = int(cmd[1]) if len(cmd) > 1 else 0
                        return exit_code
                    elif found_command["long"] == "help":
                        print_help (commands)
                    elif found_command["long"] == "reload":
                        import_commands (reload=True)
                    else:
                        navigation_suggestions = found_command["module"].run(cmd, context, ui_state)

        except Exception as e:
            if have_non_interactive_commands or type(e) == util.TTFatalException:
                # In non-interactive mode and on fatal excepions, we re-raise to exit the program
                raise
            else:
                # Otherwise, we print the call stack, but continue the REPL
                util.notify_exception (type(e), e, e.__traceback__)
    return 0

# Import 'plugin' commands from debuda_commands directory
# With reload=True, the debuda_commands can be live-reloaded (importlib.reload)
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
            util.ERROR (f"Error in module '{module_path}': {e}")
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


if __name__ == '__main__':
    parser=get_parser()
    args = parser.parse_args()

    if not args.verbose:
        util.VERBOSE=util.NULL_PRINT

    if args.output_dir is None: # Then find the most recent tt_build subdir
        args.output_dir = locate_output_dir()

    if args.output_dir is None:
        util.FATAL (f"Output directory (output_dir) was not supplied and cannot be determined automatically. Exiting...")

    # Try to connect to the server
    server_ifc = tt_device.init_server_communication(args)

    # Create the context
    context = load_context (netlist_filepath = args.netlist, run_dirpath=args.output_dir)
    args.path_to_runtime_yaml = context.netlist.runtime_data_yaml.filepath
    context.server_ifc = server_ifc
    context.args = args
    context.debuda_path = __file__

    # If we spawned debuda stub, the runtime_data provided by debuda stub is not valid, and we use the runtime_data.yaml file saved by the test
    if server_ifc.spawning_debuda_stub:
        server_ifc.get_runtime_data = lambda: context.netlist.runtime_data_yaml

    # Main function
    exit_code = main(args, context)

    util.INFO (f"Exiting with code {exit_code} ")
    sys.exit (exit_code)
