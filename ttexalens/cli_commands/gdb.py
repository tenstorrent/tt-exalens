# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  gdb start --port <port>
  gdb stop

Description:
  Starts or stops gdb server.

Examples:
  gdb start --port 6767
  gdb stop
"""

from ttexalens.uistate import UIState
from ttexalens import command_parser, util as util

command_metadata = {
    "short": "gdb",
    "type": "high-level",
    "description": __doc__,
    "context": ["limited", "metal"],
}


def run(cmd_text, context, ui_state: UIState):
    dopt = command_parser.tt_docopt(
        command_metadata["description"],
        argv=cmd_text.split()[1:],
    )

    if dopt.args["start"]:
        try:
            port = int(dopt.args["<port>"])
            ui_state.start_gdb(port)
        except:
            util.ERROR("Invalid port number")
    elif dopt.args["stop"]:
        ui_state.stop_gdb()
    else:
        util.ERROR("Invalid command")
