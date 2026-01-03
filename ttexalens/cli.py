#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  tt-exalens [--commands=<cmds>] [--start-server=<server_port>] [--start-gdb=<gdb_port>] [-s=<simulation_directory>] [--verbosity=<verbosity>] [--test] [--jtag] [--use-noc1] [--disable-4B-mode]
  tt-exalens --server [--port=<port>] [--test] [--jtag] [-s=<simulation_directory>] [--background] [--use-noc1]
  tt-exalens --remote [--remote-address=<ip:port>] [--commands=<cmds>] [--start-gdb=<gdb_port>] [--verbosity=<verbosity>] [--test] [--disable-4B-mode]
  tt-exalens --gdb [gdb_args...]
  tt-exalens -h | --help
  tt-exalens --version

Options:
  -h --help                       Show this help message and exit.
  --version                       Show version and exit.
  --server                        Start a TTExaLens server. If not specified, the port will be set to 5555.
  --remote                        Attach to the remote TTExaLens server. If not specified, IP defaults to localhost and port to 5555.
  --port=<port>                   Port of the TTExaLens server. If not specified, defaults to 5555.  [default: 5555]
  --remote-address=<ip:port>      Address of the remote TTExaLens server, in the form of ip:port, or just :port, if ip is localhost. If not specified, defaults to localhost:5555. [default: localhost:5555]
  --commands=<cmds>               Execute a list of semicolon-separated commands.
  --start-gdb=<gdb_port>          Start a gdb server on the specified port.
  --start-server=<server_port>    Start a tt-exalens server on the specified port.
  --background                    Start the server in the background detached from console (doesn't require ENTER button for exit, but exit.server file to be created).
  -s=<simulation_directory>       Specifies build output directory of the simulator.
  --verbosity=<verbosity>         Choose output verbosity. 1: ERROR, 2: WARN, 3: INFO, 4: VERBOSE, 5: DEBUG. [default: 3]
  --test                          Exits with non-zero exit code on any exception.
  --jtag                          Initialize JTAG interface.
  --use-noc1                      Initialize with NOC1 and use NOC1 for communication with the device.
  --disable-4B-mode               Disable 4-byte mode for communication with the device.
  --gdb                           Start RISC-V gdb client with the specified arguments.

Description:
  TTExaLens parses the build output files and reads the device state to provide a debugging interface for the user.

  There are two modes of operation:
    1. Local mode: The user can run tt-exalens with a specific output directory. This will load the runtime data from the output directory. If the output directory is not specified, the most recent subdirectory of tt_build/ will be used.
    2. Remote mode: The user can connect to a TTExaLens server running on a remote machine. The server will provide the runtime data.

  Passing the --server flag will start a TTExaLens server. The server will listen on the specified port (default 5555) for incoming connections.
  Passing the --gdb flag will start a RISC-V gdb client. The gdb client can be used to connect to gdb server that can be start from another TTExaLens instance.
"""

try:
    import sys, os, traceback, fnmatch, importlib
    from tabulate import tabulate
    from prompt_toolkit.formatted_text import HTML
    from docopt import DocoptExit, docopt
    from fastnumbers import try_int
except ModuleNotFoundError as e:
    import traceback

    traceback.print_exc()
    print(
        f"Try:\033[31m pip install --extra-index-url https://test.pypi.org/simple/ -r ttexalens/requirements.txt \033[0m"
    )
    exit(1)


from ttexalens import init_ttexalens, init_ttexalens_remote
from ttexalens import tt_exalens_ifc
from ttexalens import server
from ttexalens import util as util
from ttexalens.context import Context
from ttexalens.uistate import UIState
from ttexalens.command_parser import tt_docopt, CommandMetadata, find_command, CommandParsingException
from ttexalens.gdb.gdb_client import get_gdb_client_path


# Creates rows for tabulate for all commands of a given type
def format_commands(commands: list[CommandMetadata], type, specific_cmd=None, verbose=False):
    rows = []
    for c in commands:
        if c.type == type and (specific_cmd is None or c.long_name == specific_cmd or c.short_name == specific_cmd):
            if verbose:
                row = [f"{util.CLR_INFO}{c.long_name}{util.CLR_END}", f"{c.short_name}", ""]
                rows.append(row)
                row2 = [f"", f"", f"{c.description}"]
                rows.append(row2)
                rows.append(["<--MIDRULE-->", "", ""])
            else:
                descriptions = c.description.split("\n") if c.description is not None else []
                # Iterate to find the line containing "Description:". Then take the following line.
                # If there is no such line, take the first line.
                found_description = False
                description = ""
                for line in descriptions:
                    if found_description:
                        description = line
                        break
                    if "Description:" in line:
                        found_description = True
                if not found_description:
                    description = descriptions[0]
                description = description.strip()
                row = [
                    f"{util.CLR_INFO}{c.long_name}{util.CLR_END}",
                    f"{c.short_name}",
                    f"{description}",
                ]
                rows.append(row)
    return rows


# Print all commands (help)
def print_help(commands: list[CommandMetadata], cmd):
    help_command = find_command(commands, "help")
    assert help_command is not None and help_command.description is not None
    args = tt_docopt(help_command, " ".join(cmd)).args

    specific_cmd = args["<command>"] if "<command>" in args else None
    verbose = ("-v" in args and args["-v"]) or specific_cmd is not None

    rows = []
    rows += format_commands(commands, "housekeeping", specific_cmd, verbose)
    rows += format_commands(commands, "low-level", specific_cmd, verbose)
    rows += format_commands(commands, "high-level", specific_cmd, verbose)
    if args["--all"]:
        rows += format_commands(commands, "dev", specific_cmd, verbose)

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


# Imports 'plugin' commands from cli_commands/ directory
# With 'reload' argument set to True, the cli_commands can be live-reloaded (using importlib.reload)
def import_commands(reload: bool = False) -> list[CommandMetadata]:
    # Built-in commands
    commands = [
        CommandMetadata(
            long_name="exit",
            short_name="x",
            type="housekeeping",
            description="Description:\n  Exits the program. The optional argument represents the exit code. Defaults to 0.",
            context=["util"],
        ),
        CommandMetadata(
            long_name="help",
            short_name="h",
            type="housekeeping",
            description="Usage:\n  help [-v] [--all] [<command>]\n\n"
            + "Description:\n  Prints documentation summary. Use -v for details. If a command name is specified, it prints documentation for that command only.\n\n"
            + "Options:\n  -v      If specified, prints verbose documentation.\n  --all   If specified, prints all commands.\n",
            context=["util"],
        ),
        CommandMetadata(
            long_name="reload",
            short_name="rl",
            type="housekeeping",
            description="Description:\n  Reloads files in cli_commands directory. Useful for development of commands.",
            context=["util"],
        ),
        CommandMetadata(
            long_name="eval",
            short_name="ev",
            type="dev",
            description="Description:\n  Evaluates a Python expression.\n\nExamples:\n  eval 3+5\n  eval hex(@brisc.EPOCH_INFO_PTR.epoch_id)",
            context=["util"],
        ),
    ]

    cmd_files = []
    for root, dirnames, filenames in os.walk(util.application_path() + "/cli_commands"):
        for filename in fnmatch.filter(filenames, "*.py"):
            cmd_files.append(os.path.join(root, filename))

    sys.path.append(util.application_path() + "/cli_commands")

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
        command_metadata: CommandMetadata = cmd_module.command_metadata
        command_metadata._module = cmd_module

        # Make the module name the default 'long' invocation string
        if not command_metadata.long_name:
            command_metadata.long_name = cmd_module.__name__
        util.VERBOSE(f"Importing command {command_metadata.long_name} from '{cmd_module.__name__}'")

        if reload:
            importlib.reload(cmd_module)

        # Check command names/shortcut overlap (only when not reloading)
        for cmd in commands:
            if cmd.long_name == command_metadata.long_name:
                util.FATAL(f"Command {cmd.long_name} already exists")
            if cmd.short_name == command_metadata.short_name:
                util.FATAL(
                    f"Commands {cmd.long_name} and {command_metadata.long_name} use the same shortcut: {cmd.short_name}"
                )
        dopt = tt_docopt(command_metadata, command_metadata.long_name)
        command_metadata = command_metadata.copy()
        command_metadata.description = dopt.doc
        commands.append(command_metadata)
    return commands


def extract_command_file_output(command_text: str) -> str | None:
    # Check if command ends with '>file_name' or '>>file_name' or '|>file_name' or '|>>file_name' where file_name can have space at the start
    import re

    regex_pattern = r"((\|)?(>)?>[ ]*([^ ]+|\"[^\"]*\"|'[^']*')+)$"
    match = re.search(regex_pattern, command_text)
    if match:
        return match.group(1)
    return None


def redirect_command_output_to_file(file_output: str | None):
    if file_output is None:
        return util.redirect_output_to_file_and_terminal(None)

    show_terminal_output = True
    if file_output.startswith("|"):
        show_terminal_output = False
        file_output = file_output[1:]

    append = False
    if file_output.startswith(">>"):
        append = True
        file_output = file_output[2:]
    else:
        assert file_output.startswith(">")
        file_output = file_output[1:]

    file_output = file_output.strip()
    file_output = file_output.replace('"', "").replace("'", "")
    return util.redirect_output_to_file_and_terminal(file_output, show_terminal_output, append)


def main_loop(args, context: Context):
    """
    Main loop: read-eval-print
    """
    cmd_raw = ""

    context.assign_commands(
        import_commands()
    )  # Set the commands in the context so we can call commands from other commands

    # Initialize current UI state
    ui_state = UIState(context)

    navigation_suggestions = None

    # Check if we need to start server
    if args["--start-server"]:
        port = int(args["--start-server"])
        ui_state.start_server(port)

    # Check if we need to start gdb server
    if args["--start-gdb"]:
        port = int(args["--start-gdb"])
        ui_state.start_gdb(port)

    # These commands will be executed right away (before allowing user input)
    non_interactive_commands = args["--commands"].split(";") if args["--commands"] else []

    # Main command loop
    try:
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

                    def get_dynamic_prompt() -> HTML:
                        my_prompt = ""
                        if ui_state.ttexalens_server is not None:
                            server_status = f"{util.CLR_PROMPT}{ui_state.ttexalens_server.port}{util.CLR_PROMPT_END}"
                            my_prompt += f"server:{server_status} "
                        if ui_state.gdb_server is not None:
                            gdb_status = f"{util.CLR_PROMPT}{ui_state.gdb_server.server.port}{util.CLR_PROMPT_END}"
                            if ui_state.gdb_server.is_connected:
                                gdb_status += "(connected)"
                            my_prompt += f"gdb:{gdb_status} "
                        if ui_state.context.use_4B_mode:
                            my_prompt += f"{util.CLR_PROMPT}[4B MODE] {util.CLR_PROMPT_END}"
                        noc_prompt = "1" if ui_state.context.use_noc1 else "0"
                        if ui_state.current_device.is_blackhole() or ui_state.current_device.is_wormhole():
                            my_prompt += f"noc:{util.CLR_PROMPT}{noc_prompt}{util.CLR_PROMPT_END} "
                        jtag_prompt = "JTAG" if ui_state.current_device._has_jtag else ""
                        device_id = f"{ui_state.current_device_id}"
                        # TODO (#617): Once we figure out do we want to show unique_id in prompt, uncomment following lines
                        # if ui_state.current_device.unique_id is not None:
                        #     device_id += f" [0x{ui_state.current_device.unique_id:x}]"
                        my_prompt += f"device:{util.CLR_PROMPT}{jtag_prompt}{device_id}{util.CLR_PROMPT_END} "
                        my_prompt += f"loc:{util.CLR_PROMPT}{current_loc.to_user_str()}{util.CLR_PROMPT_END} "
                        my_prompt += f"{ui_state.current_prompt}> "
                        return HTML(my_prompt)

                    cmd_raw = ui_state.prompt(get_dynamic_prompt)

                # Trim comments
                cmd_raw = cmd_raw.split("#")[0].strip()

                # Check if command should be serialized to a file
                file_output = extract_command_file_output(cmd_raw)
                if file_output is not None:
                    cmd_raw = cmd_raw[: -len(file_output)].strip()

                with redirect_command_output_to_file(file_output) as terminal_override:
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
                            if c.short_name == cmd_string or c.long_name == cmd_string:
                                found_command = c
                                break

                        if found_command == None:
                            # Print help on invalid commands
                            print_help(context.commands, cmd)
                            raise util.TTException(f"Invalid command '{cmd_string}'")
                        else:
                            if found_command.long_name == "exit":
                                exit_code = int(cmd[1]) if len(cmd) > 1 else 0
                                return exit_code
                            elif found_command.long_name == "help":
                                print_help(context.commands, cmd)
                            elif found_command.long_name == "reload":
                                import_commands(reload=True)
                            elif found_command.long_name == "eval":
                                eval_str = " ".join(cmd[1:])
                                print(f"{eval_str} = {eval(eval_str)}")
                            else:
                                assert found_command._module is not None
                                new_navigation_suggestions = found_command._module.run(cmd_raw, context, ui_state)
                                navigation_suggestions = new_navigation_suggestions

            except CommandParsingException as e:
                if e.is_parsing_error():
                    util.ERROR(e)
                    if args["--test"]:  # Always raise in test mode
                        raise
                elif e.is_help_message():
                    # help is automatically printed by command parser
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
            except DocoptExit as e:
                if args["--test"]:  # Always raise in test mode
                    util.ERROR("CLI option --test is set. Raising exception to exit.")
                    raise
                else:
                    print(e.usage)
    finally:
        # Do best effort cleanup before exiting
        try:
            ui_state.stop_server()
        except:
            pass
        try:
            ui_state.stop_gdb()
        except:
            pass


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--gdb":
        gdb_client_path = get_gdb_client_path()
        gdb_client_args = sys.argv[2:]

        # Start gdb client with the specified arguments
        import subprocess

        subprocess.run([gdb_client_path] + gdb_client_args)
        return

    args = docopt(__doc__)

    if args["--version"]:
        import importlib.metadata as importlib_metadata

        try:
            installed_version = importlib_metadata.version("tt-exalens")
            print(f"tt-exalens version {installed_version}")
        except importlib_metadata.PackageNotFoundError:
            print("tt-exalens version not found (not installed via pip)")
            # Alternatively, read from VERSION file
            with open(os.path.join(util.application_path(), "../VERSION"), "r") as version_file:
                version = version_file.read().strip()
            print(f"tt-exalens version from VERSION file: {version}")
        return

    # SETTING VERBOSITY
    try:
        verbosity = int(args["--verbosity"])
        util.Verbosity.set(verbosity)
    except:
        util.WARN("Verbosity level must be an integer. Falling back to default value.")
    util.VERBOSE(f"Verbosity level: {util.Verbosity.get().name} ({util.Verbosity.get().value})")

    # Try to start the server. If already running, exit with error.
    if args["--server"]:
        if args["--background"]:
            communicator = tt_exalens_ifc.local_init(
                init_jtag=args["--jtag"],
                initialize_with_noc1=args["--use-noc1"],
                simulation_directory=args["-s"],
            )
            ttexalens_server = server.start_server(port=int(args["--port"]), communicator=communicator)

            util.INFO("The debug server is running in the background.")
            util.INFO("To stop the server, use the command: touch exit.server")

            # Remove exit.server file if it exists
            if os.path.exists("exit.server"):
                os.remove("exit.server")
            try:
                # Wait until exit.server file is created to exit the program
                while not os.path.isfile("exit.server"):
                    import time

                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            ttexalens_server.stop()
            return
        else:
            args["--start-server"] = args["--port"]

    if args["--remote"]:
        address = args["--remote-address"].split(":")
        server_ip = address[0] if address[0] != "" else "localhost"
        server_port = address[-1]
        util.INFO(f"Connecting to TTExaLens server at {server_ip}:{server_port}")
        use_4B_mode = False if args["--disable-4B-mode"] else True
        context = init_ttexalens_remote(server_ip, int(server_port), use_4B_mode)
    else:
        context = init_ttexalens(
            init_jtag=args["--jtag"],
            use_noc1=args["--use-noc1"],
            use_4B_mode=False if args["--disable-4B-mode"] else True,
            simulation_directory=args["-s"],
        )

    # Main function
    exit_code = main_loop(args, context)

    util.VERBOSE(f"Exiting with code {exit_code} ")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
