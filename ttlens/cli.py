#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  tt-lens [--commands=<cmds>] [--write-cache] [--cache-path=<path>] [--start-gdb=<gdb_port>] [--devices=<devices>] [--verbosity=<verbosity>] [--test] [--jtag]
  tt-lens --server [--port=<port>] [--devices=<devices>] [--test] [--jtag] [-s=<simulation_directory>] [--background]
  tt-lens --remote [--remote-address=<ip:port>] [--commands=<cmds>] [--write-cache] [--cache-path=<path>] [--start-gdb=<gdb_port>] [--verbosity=<verbosity>] [--test]
  tt-lens --cached [--cache-path=<path>] [--commands=<cmds>] [--verbosity=<verbosity>] [--test]
  tt-lens -h | --help

Options:
  -h --help                       Show this help message and exit.
  --server                        Start a TTLens server. If not specified, the port will be set to 5555.
  --remote                        Attach to the remote TTLens server. If not specified, IP defaults to localhost and port to 5555.
  --cached                        Use the cache from previous TTLens run to simulate device communication.
  --port=<port>                   Port of the TTLens server. If not specified, defaults to 5555.  [default: 5555]
  --remote-address=<ip:port>      Address of the remote TTLens server, in the form of ip:port, or just :port, if ip is localhost. If not specified, defaults to localhost:5555. [default: localhost:5555]
  --commands=<cmds>               Execute a list of semicolon-separated commands.
  --start-gdb=<gdb_port>          Start a gdb server on the specified port.
  --write-cache                   Write the cache to disk.
  --cache-path=<path>             If running in --cached mode, this is the path to the cache file. If writing cache, this is the path for output. [default: ttlens_cache.pkl]
  --devices=<devices>             Comma-separated list of devices to load. If not supplied, all devices will be loaded.
  --background                    Start the server in the background detached from console (doesn't require ENTER button for exit, but exit.server file to be created).
  -s=<simulation_directory>       Specifies build output directory of the simulator.
  --verbosity=<verbosity>         Choose output verbosity. 1: ERROR, 2: WARN, 3: INFO, 4: VERBOSE, 5: DEBUG. [default: 3]
  --test                          Exits with non-zero exit code on any exception.
  --jtag                          Initialize JTAG interface.

Description:
  TTLens parses the build output files and reads the device state to provide a debugging interface for the user.

  There are three modes of operation:
    1. Local mode: The user can run tt-lens with a specific output directory. This will load the runtime data from the output directory. If the output directory is not specified, the most recent subdirectory of tt_build/ will be used.
    2. Remote mode: The user can connect to a TTLens server running on a remote machine. The server will provide the runtime data.
    3. Cached mode: The user can use a cache file from previous TTLens run. This is useful for debugging without a connection to the device. Writing is disabled in this mode.

  Passing the --server flag will start a TTLens server. The server will listen on the specified port (default 5555) for incoming connections.
"""

try:
    import sys, os, traceback, fnmatch, importlib
    from tabulate import tabulate
    from prompt_toolkit import PromptSession
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.formatted_text import HTML, fragment_list_to_text, to_formatted_text
    from prompt_toolkit.history import InMemoryHistory
    from docopt import DocoptExit, docopt
    from fastnumbers import try_int
except ModuleNotFoundError as e:
    traceback.print_exc()
    print(f"Try:\033[31m pip install -r ttlens/requirements.txt \033[0m")
    exit(1)


from ttlens import tt_lens_init
from ttlens import tt_lens_server
from ttlens import util as util
from ttlens.uistate import UIState
from ttlens.commands import find_command, CommandParsingException

from ttlens import Verbosity


class TTLensCompleter(Completer):
    def __init__(self, commands, context):
        self.commands = [cmd["long"] for cmd in commands] + [cmd["short"] for cmd in commands]
        self.context = context

    # Given a piece of a command, find all possible completions
    def lookup_commands(self, cmd):
        completions = []
        for command in self.commands:
            if command.startswith(cmd):
                completions.append(command)
        return completions

    def fuzzy_lookup_addresses(self, addr):
        completions = self.context.elf.fuzzy_find_multiple(addr, limit=30)
        return completions

    def get_completions(self, document, complete_event):
        if complete_event.completion_requested:
            prompt_current_word = document.get_word_before_cursor(pattern=self.context.elf.name_word_pattern)
            prompt_text = document.text_before_cursor
            # 1. If it is the first word, complete with the list of commands (lookup_commands)
            if " " not in prompt_text:
                for command in self.lookup_commands(prompt_current_word):
                    yield Completion(command, start_position=-len(prompt_current_word))
            # 2. If the currently-edited word starts with @, complete with address lookup from FW (fuzzy_lookup_addresses)
            elif prompt_current_word.startswith("@"):
                addr_part = prompt_current_word[1:]
                for address in self.fuzzy_lookup_addresses(addr_part):
                    yield Completion(f"@{address}", start_position=-len(prompt_current_word))


# Creates rows for tabulate for all commands of a given type
def format_commands(commands, type, specific_cmd=None, verbose=False):
    rows = []
    for c in commands:
        if c["type"] == type and (specific_cmd is None or c["long"] == specific_cmd or c["short"] == specific_cmd):
            description = c["description"]
            if verbose:
                row = [f"{util.CLR_INFO}{c['long']}{util.CLR_END}", f"{c['short']}", ""]
                rows.append(row)
                row2 = [f"", f"", f"{description}"]
                rows.append(row2)
                rows.append(["<--MIDRULE-->", "", ""])
            else:
                description = description.split("\n")
                # Iterate to find the line containing "Description:". Then take the following line.
                # If there is no such line, take the first line.
                found_description = False
                for line in description:
                    if found_description:
                        description = line
                        break
                    if "Description:" in line:
                        found_description = True
                if not found_description:
                    description = description[0]
                description = description.strip()
                row = [
                    f"{util.CLR_INFO}{c['long']}{util.CLR_END}",
                    f"{c['short']}",
                    f"{description}",
                ]
                rows.append(row)
    return rows


# Print all commands (help)
def print_help(commands, cmd):
    help_command_description = find_command(commands, "help")["description"]
    args = docopt(help_command_description, argv=" ".join(cmd[1:]))

    specific_cmd = args["<command>"] if "<command>" in args else None
    verbose = ("-v" in args and args["-v"]) or specific_cmd is not None

    rows = []
    rows += format_commands(commands, "housekeeping", specific_cmd, verbose)
    rows += format_commands(commands, "low-level", specific_cmd, verbose)
    rows += format_commands(commands, "high-level", specific_cmd, verbose)
    # rows += format_commands (commands, 'dev', "Development")

    if not rows:
        util.WARN(f"Command '{specific_cmd}' not found")
        return

    # Replace each line starting with <--MIDRULE-->, with a ruler line to separate the commands visually
    table_str = tabulate(rows, headers=["Full Name", "Short", "Description"], disable_numparse=True)
    lines = table_str.split("\n")
    midrule = lines[1]
    for i in range(len(lines)):
        if lines[i].startswith("<--MIDRULE-->"):
            lines[i] = midrule
    new_table_str = "\n".join(lines)
    print(new_table_str)
    if not verbose:
        print("Use '-v' for more details.")


# Certain commands give suggestions for next step. This function formats and prints those suggestions.
def print_navigation_suggestions(navigation_suggestions):
    if navigation_suggestions:
        print("Speed dial:")
        rows = []
        for i in range(len(navigation_suggestions)):
            rows.append(
                [
                    f"{i}",
                    f"{navigation_suggestions[i]['description']}",
                    f"{navigation_suggestions[i]['cmd']}",
                ]
            )
        print(tabulate(rows, headers=["#", "Description", "Command"], disable_numparse=True))


# Imports 'plugin' commands from ttlens_commands/ directory
# With 'reload' argument set to True, the ttlens_commands can be live-reloaded (using importlib.reload)
def import_commands(reload=False):
    # Built-in commands
    commands = [
        {
            "long": "exit",
            "short": "x",
            "type": "housekeeping",
            "description": "Description:\n  Exits the program. The optional argument represents the exit code. Defaults to 0.",
            "context": "util",
        },
        {
            "long": "help",
            "short": "h",
            "type": "housekeeping",
            "description": "Usage:\n  help [-v] [<command>]\n\n"
            + "Description:\n  Prints documentation summary. Use -v for details. If a command name is specified, it prints documentation for that command only.\n\n"
            + "Options:\n  -v   If specified, prints verbose documentation.",
            "context": "util",
        },
        {
            "long": "reload",
            "short": "rl",
            "type": "housekeeping",
            "description": "Description:\n  Reloads files in ttlens_commands directory. Useful for development of commands.",
            "context": "util",
        },
        {
            "long": "eval",
            "short": "ev",
            "type": "dev",
            "description": "Description:\n  Evaluates a Python expression.\n\nExamples:\n  eval 3+5\n  eval hex(@brisc.EPOCH_INFO_PTR.epoch_id)",
            "context": "util",
        },
    ]

    cmd_files = []
    for root, dirnames, filenames in os.walk(util.application_path() + "/ttlens_commands"):
        for filename in fnmatch.filter(filenames, "*.py"):
            cmd_files.append(os.path.join(root, filename))

    sys.path.append(util.application_path() + "/ttlens_commands")

    cmd_files.sort()
    for cmdfile in cmd_files:
        module_path = os.path.splitext(os.path.basename(cmdfile))[0]
        if module_path == "__init__":
            continue
        try:
            cmd_module = importlib.import_module(module_path)
        except Exception as e:
            # Print call stack
            util.notify_exception(type(e), e, e.__traceback__)
            continue
        command_metadata = cmd_module.command_metadata
        command_metadata["module"] = cmd_module

        # Make the module name the default 'long' invocation string
        if "long" not in command_metadata:
            command_metadata["long"] = cmd_module.__name__
        util.VERBOSE(f"Importing command {command_metadata['long']} from '{cmd_module.__name__}'")

        if reload:
            importlib.reload(cmd_module)

        # Check command names/shortcut overlap (only when not reloading)
        for cmd in commands:
            if cmd["long"] == command_metadata["long"]:
                util.FATAL(f"Command {cmd['long']} already exists")
            if cmd["short"] == command_metadata["short"]:
                util.FATAL(
                    f"Commands {cmd['long']} and {command_metadata['long']} use the same shortcut: {cmd['short']}"
                )
        commands.append(command_metadata)
    return commands


class SimplePromptSession:
    def __init__(self):
        self.history = InMemoryHistory()

    def prompt(self, message):
        print(fragment_list_to_text(to_formatted_text(message)))
        s = input()
        self.history.append_string(s)
        return s


def main_loop(args, context):
    """
    Main loop: read-eval-print
    """
    cmd_raw = ""

    context.filter_commands(
        import_commands()
    )  # Set the commands in the context so we can call commands from other commands

    # Create prompt object.
    context.prompt_session = (
        PromptSession(completer=TTLensCompleter(context.commands, context))
        if sys.stdin.isatty()
        else SimplePromptSession()
    )

    # Initialize current UI state
    ui_state = UIState(context)

    navigation_suggestions = None

    # Check if we need to start gdb server
    if args["--start-gdb"]:
        port = int(args["--start-gdb"])
        print(f"Starting gdb server on port {port}")
        ui_state.start_gdb(port)

    # These commands will be executed right away (before allowing user input)
    non_interactive_commands = args["--commands"].split(";") if args["--commands"] else []

    # Main command loop
    while True:
        have_non_interactive_commands = len(non_interactive_commands) > 0
        current_loc = ui_state.current_location

        try:
            print_navigation_suggestions(navigation_suggestions)

            if have_non_interactive_commands:
                cmd_raw = non_interactive_commands[0].strip()
                non_interactive_commands = non_interactive_commands[1:]
                if len(cmd_raw) > 0:
                    print(f"{util.CLR_INFO}Executing command: %s{util.CLR_END}" % cmd_raw)
            else:
                if ui_state.gdb_server is None:
                    gdb_status = f"{util.CLR_PROMPT_BAD_VALUE}None{util.CLR_PROMPT_BAD_VALUE_END}"
                else:
                    gdb_status = f"{util.CLR_PROMPT}{ui_state.gdb_server.server.port}{util.CLR_PROMPT_END}"
                    # TODO: Since we cannot update status during prompt, this is commented out for now
                    # if ui_state.gdb_server.is_connected:
                    #     gdb_status += "(connected)"
                my_prompt = f"gdb:{gdb_status} "
                jtag_prompt = "JTAG" if ui_state.current_device._has_jtag else ""
                my_prompt += f"device:{util.CLR_PROMPT}{jtag_prompt}{ui_state.current_device_id}{util.CLR_PROMPT_END} "
                my_prompt += f"loc:{util.CLR_PROMPT}{current_loc.to_user_str()}{util.CLR_PROMPT_END} "
                my_prompt += f"{ui_state.current_prompt}> "
                cmd_raw = context.prompt_session.prompt(HTML(my_prompt))

            cmd_int = try_int(cmd_raw)
            if type(cmd_int) == int:
                if navigation_suggestions and cmd_int >= 0 and cmd_int < len(navigation_suggestions):
                    cmd_raw = navigation_suggestions[cmd_int]["cmd"]
                else:
                    raise util.TTException(f"Invalid speed dial number: {cmd_int}")

            cmd = cmd_raw.split()
            if len(cmd) > 0:
                cmd_string = cmd[0]
                found_command = None

                # Look for command to execute
                for c in context.commands:
                    if c["short"] == cmd_string or c["long"] == cmd_string:
                        found_command = c

                if found_command == None:
                    # Print help on invalid commands
                    print_help(context.commands, cmd)
                    raise util.TTException(f"Invalid command '{cmd_string}'")
                else:
                    if found_command["long"] == "exit":
                        exit_code = int(cmd[1]) if len(cmd) > 1 else 0
                        return exit_code
                    elif found_command["long"] == "help":
                        print_help(context.commands, cmd)
                    elif found_command["long"] == "reload":
                        import_commands(reload=True)
                    elif found_command["long"] == "eval":
                        eval_str = " ".join(cmd[1:])
                        eval_str = context.elf.substitute_names_with_values(eval_str)
                        print(f"{eval_str} = {eval(eval_str)}")
                    else:
                        new_navigation_suggestions = found_command["module"].run(cmd_raw, context, ui_state)
                        navigation_suggestions = new_navigation_suggestions

        except CommandParsingException as e:
            if e.is_parsing_error():
                util.ERROR(e)
                if args["--test"]:  # Always raise in test mode
                    raise
            elif e.is_help_message():
                # help is automatically printed by command parserr
                pass
            else:
                raise
        except Exception as e:
            if args["--test"]:  # Always raise in test mode
                util.ERROR("CLI option --test is set. Raising exception to exit.")
                raise
            else:
                util.notify_exception(type(e), e, e.__traceback__)
            if have_non_interactive_commands or type(e) == util.TTFatalException:
                # In non-interactive mode and on fatal excepions, we re-raise to exit the program
                raise


def main():
    args = docopt(__doc__)

    # SETTING VERBOSITY
    try:
        verbosity = int(args["--verbosity"])
        Verbosity.set(verbosity)
    except:
        util.WARN("Verbosity level must be an integer. Falling back to default value.")
    util.VERBOSE(f"Verbosity level: {Verbosity.get().name} ({Verbosity.get().value})")

    wanted_devices = None
    if args["--devices"]:
        wanted_devices = args["--devices"].split(",")
        wanted_devices = [int(d) for d in wanted_devices]

    cache_path = None
    if args["--write-cache"]:
        cache_path = args["--cache-path"]

    # Try to start the server. If already running, exit with error.
    if args["--server"]:
        print(f"Starting TTLens server at {args['--port']}")
        ttlens_server = tt_lens_server.start_server(args["--port"], wanted_devices, init_jtag=args["--jtag"])
        if args["--test"]:
            while True:
                pass
        input("Press Enter to exit server...")
        tt_lens_server.stop_server(ttlens_server)
        sys.exit(0)

    if args["--cached"]:
        util.INFO(f"Starting TTLens from cache.")
        context = tt_lens_init.init_ttlens_cached(args["--cache-path"])
    elif args["--remote"]:
        address = args["--remote-address"].split(":")
        server_ip = address[0] if address[0] != "" else "localhost"
        server_port = address[-1]
        util.INFO(f"Connecting to TTLens server at {server_ip}:{server_port}")
        context = tt_lens_init.init_ttlens_remote(server_ip, int(server_port), cache_path)
    else:
        context = tt_lens_init.init_ttlens(wanted_devices, cache_path, args["--jtag"])

    # Main function
    exit_code = main_loop(args, context)

    util.VERBOSE(f"Exiting with code {exit_code} ")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
