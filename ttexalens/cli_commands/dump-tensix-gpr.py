# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-tensix-gpr [ -t <thread-id> ] [ -d <device> ] [ -l <loc> ]

Options:
  -t <thread-id>  Thread ID. Options: [0, 1, 2] Default: all
  -d <device>     Device ID. Optional. Default: current device
  -l <loc>        Core location in X-Y or R,C format. Default: current core

Description:
  Prints the tensix GPR for given thread ID, at the specified location and device.

Examples:
tgpr
tgpr -t 0
tgpr -d 0
tgpr -l 0,0
tgpr -t 0 -d 0 -l 0,0
"""

from tabulate import tabulate
from ttexalens import command_parser
from ttexalens.hardware.wormhole.functional_worker_registers import get_general_purpose_registers
from ttexalens.uistate import UIState
from ttexalens.util import put_table_list_side_by_side


command_metadata = {
    "short": "tgpr",
    "long": "dump-tensix-gpr",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "command_option_names": ["--device", "--loc"],
}


def run(cmd_text, context, ui_state: UIState):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    thread_ids = [int(dopt.args["<thread_id>"])] if dopt.args["-t"] else [0, 1, 2]
    for device in dopt.for_each("--device", context, ui_state):
        gpr_registers = get_general_purpose_registers()
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            register_store = device.get_block(loc).get_register_store()
            tables: list[str] = []
            for thread_id in thread_ids:
                registers = gpr_registers[thread_id]
                gpr_data: dict[str, int] = {
                    register_name: register_store.read_register(register_store.registers[register_name])
                    for register_name in registers
                }
                table = [[register_name, gpr_data[register_name]] for register_name in gpr_data.keys()]
                tables.append(tabulate(table, headers=[f"Thread {thread_id}", "Values"], tablefmt="simple_outline"))
            print(put_table_list_side_by_side(tables))

    return None
