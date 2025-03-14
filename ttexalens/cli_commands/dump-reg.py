# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  dump-reg [ -d <device> ] [ -l <loc> ]

Options:
  -d <device>   Device ID. Optional. Default: current device
  -l <loc>      Core location in X-Y or R,C format. Default: current core

Description:
  Prints the specified register, at the specified location and device.

Examples:
    dreg
    dreg -d 0 -l 0,0
    dreg -l 0,0
    dreg -d 0
"""

command_metadata = {
    "short": "dreg",
    "type": "low-level",
    "description": __doc__,
    "context": ["limited", "metal"],
    "command_option_names": ["--device", "--loc"],
}

from ttexalens.uistate import UIState
from ttexalens.debug_tensix import TensixDebug
from ttexalens.device import Device
from ttexalens import command_parser


def run(cmd_text, context, ui_state: UIState = None):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    for device in dopt.for_each("--device", context, ui_state):
        for loc in dopt.for_each("--loc", context, ui_state, device=device):
            pass
