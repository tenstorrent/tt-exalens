# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
    go [-m <mode>] [-n <noc>] [ -d <device> ] [ -l <loc> ]

Description:
    Sets the current device/location/noc/4B mode.

Options:
    -m <mode>    Use 4B mode for communication with the device. [0: False, 1: True]
    -n <noc>     Use NOC1 or NOC0 for communication with the device. [0: NOC0, 1: NOC1]

Examples:
    go -m 1 -n 1 -d 0 -l 0,0
"""
import ttexalens.util as util
from ttexalens.uistate import UIState
from ttexalens.context import Context
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="go",
    type="high-level",
    description=__doc__,
    common_option_names=["--device", "--loc"],
)


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)

    if dopt.args["-n"] is not None:
        noc = int(dopt.args["-n"])
        if noc not in [0, 1]:
            util.ERROR("NOC must be 0 or 1")
            return
        ui_state.context.use_noc1 = noc == 1

    if dopt.args["-m"] is not None:
        use_4B_mode = int(dopt.args["-m"])
        if use_4B_mode not in [0, 1]:
            util.ERROR("4B mode must be 0 or 1")
            return
        ui_state.context.use_4B_mode = True if use_4B_mode == 1 else False
    for device in dopt.for_each(CommonCommandOptions.Device, context, ui_state):
        ui_state.current_device_id = device.id()
        for loc in dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device):
            ui_state.current_location = loc
            break
        break
