# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
    go [-n <noc>] [ -d <device> ] [ -l <loc> ]

Description:
    Sets the current device/location.

Examples:
    go -n 1 -d 0 -l 0,0
"""
from ttexalens import command_parser
import ttexalens.util as util
from ttexalens.uistate import UIState
from ttexalens.context import Context

command_metadata = {
    "short": "go",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "common_option_names": ["--device", "--loc"],
}


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
        common_option_names=command_metadata["common_option_names"],
    )

    if dopt.args["-n"] and dopt.args["<noc>"] is not None:
        noc = int(dopt.args["<noc>"])
        if noc not in [0, 1]:
            util.ERROR("NOC must be 0 or 1")
            return
        ui_state.context.use_noc1 = noc == 1

    for device in dopt.for_each("--device", context, ui_state):
        ui_state.current_device_id = device.id()
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            ui_state.current_location = loc
            break
        break
