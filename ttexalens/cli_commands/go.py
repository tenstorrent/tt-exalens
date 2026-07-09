# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
    go [-n <noc>] [ -d <device> ] [ -l <noc-loc> ]
    go <noc-loc> [-n <noc>] [ -d <device> ]

Description:
    Sets the current device/location/noc.
Arguments:
    noc-loc     Optional. X-Y or R,C, or dram channel (e.g. ch3). Use interchangeably with -l <loc>.

Options:
    -n <noc>     NOC to use for communication with the device. Accepts a number or name (case-insensitive): 0/NOC0, 1/NOC1, 2/SYSTEM_NOC.

Examples:
    go -n 1 -d 0 -l 0,0
"""
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import Device
import ttexalens.util as util
from ttexalens.uistate import UIState
from ttexalens.context import Context, to_noc_id
from ttexalens.command_parser import CommandMetadata, tt_docopt, CommonCommandOptions

command_metadata = CommandMetadata(
    short_name="go",
    type="high-level",
    description=__doc__,
    common_option_names=[CommonCommandOptions.Device, CommonCommandOptions.Location],
)


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    args = dopt.args

    noc_loc_str: str | None = args["<noc-loc>"]

    if args["-n"] is not None:
        try:
            ui_state.context.noc_id = to_noc_id(args["-n"])
        except ValueError as e:
            util.ERROR(str(e))
            return

    device: Device = next(dopt.for_each(CommonCommandOptions.Device, context, ui_state))
    ui_state.current_device_id = device.id

    loc: OnChipCoordinate = (
        OnChipCoordinate.create(noc_loc_str, device=device)
        if noc_loc_str
        else next(dopt.for_each(CommonCommandOptions.Location, context, ui_state, device=device))
    )
    ui_state.current_location = loc
