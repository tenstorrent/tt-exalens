# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  server start [--port <port>]
  server stop

Description:
  Starts or stops tt-exalens server.

Examples:
  server start --port 5555
  server stop
"""

from ttexalens.uistate import UIState
from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, tt_docopt

command_metadata = CommandMetadata(
    short_name="server",
    type="high-level",
    description=__doc__,
)


def run(cmd_text, context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    if dopt.args["start"]:
        try:
            port = int(dopt.args["<port>"]) if dopt.args["<port>"] else None
            ui_state.start_server(port)
        except:
            util.ERROR("Invalid port number")
    elif dopt.args["stop"]:
        ui_state.stop_server()
    else:
        util.ERROR("Invalid command")
