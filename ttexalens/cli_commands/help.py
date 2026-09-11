# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
    help [--all] [-v] [<command>]

Description:
    Prints documentation summary. Use -v for details. If a command name is specified, it prints documentation for that command only.

Options:
    -v      If specified, prints verbose documentation.
    --all   If specified, prints all commands.

Examples:
    help exit
    help -v exit
    help --all
"""
from tabulate import tabulate
import ttexalens.util as util
from ttexalens.uistate import UIState
from ttexalens.context import Context
from ttexalens.command_parser import CommandMetadata, tt_docopt

command_metadata = CommandMetadata(
    long_name="help",
    short_name="h",
    type="housekeeping",
    description=__doc__,
)


# Creates rows for tabulate for all commands of a given type
def format_commands(
    commands: list[CommandMetadata],
    type: str,
    specific_cmd: str | None = None,
    verbose: bool = False,
    ui_state: UIState | None = None,
):
    rows = []
    for c in commands:
        if c.type == type and (specific_cmd is None or c.long_name == specific_cmd or c.short_name == specific_cmd):
            # Commands that do not apply to the device in use are still listed, but in red.
            unavailable = None if ui_state is None or c.supports(ui_state) else c.unavailable_message(ui_state)
            name_color = util.CLR_ERR if unavailable else util.CLR_INFO
            if verbose:
                row = [f"{name_color}{c.long_name}{util.CLR_END}", f"{c.short_name}", ""]
                rows.append(row)
                description = f"{c.description}"
                if unavailable:
                    description = f"{util.CLR_ERR}{unavailable}{util.CLR_END}\n{description}"
                row2 = [f"", f"", description]
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
                if unavailable:
                    description = f"{description} {util.CLR_ERR}(not available on current device){util.CLR_END}"
                row = [
                    f"{name_color}{c.long_name}{util.CLR_END}",
                    f"{c.short_name}",
                    f"{description}",
                ]
                rows.append(row)
    return rows


# Print all commands (help)
def print_help(commands: list[CommandMetadata], dopt: tt_docopt, ui_state: UIState | None = None):
    args = dopt.args
    specific_cmd = args["<command>"] if "<command>" in args else None
    verbose = ("-v" in args and args["-v"]) or specific_cmd is not None

    rows = []
    rows += format_commands(commands, "housekeeping", specific_cmd, verbose, ui_state)
    rows += format_commands(commands, "low-level", specific_cmd, verbose, ui_state)
    rows += format_commands(commands, "high-level", specific_cmd, verbose, ui_state)
    if args["--all"]:
        rows += format_commands(commands, "dev", specific_cmd, verbose, ui_state)

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


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    print_help(context.commands, dopt, ui_state)
