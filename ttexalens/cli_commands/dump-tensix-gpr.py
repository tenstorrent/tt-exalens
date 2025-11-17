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
from ttexalens.uistate import UIState
from ttexalens.util import dict_to_table, put_table_list_side_by_side


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
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            register_store = device.get_block(loc).get_register_store()
            for thread_id in thread_ids:
                gpr_data = [
                    register_store.read_register(register_store.registers[f"GPR_T{thread_id}_{i}"])
                    for i in range(0, 64)
                ]
                table = [[i, gpr_data[i]] for i in range(0, len(gpr_data))]
                print(tabulate(table, headers=["Index", "Value"], disable_numparse=True))

    return None
