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

from ttexalens.context import Context
from ttexalens.uistate import UIState
from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, tt_docopt

command_metadata = CommandMetadata(
    short_name="server",
    type="high-level",
    description=__doc__,
)


def run(cmd_text: str, context: Context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    if dopt.args["start"]:
        try:
            port = int(dopt.args["<port>"]) if dopt.args["<port>"] else None
        except (TypeError, ValueError):
            util.ERROR("Invalid port number")
            return
        try:
            ui_state.start_server(port)
        except OSError as e:
            display_port = port if port is not None else 5555
            util.ERROR(f"Failed to start tt-exalens server on port {display_port}: {e}")
            return
    elif dopt.args["stop"]:
        ui_state.stop_server()
    else:
        util.ERROR("Invalid command")
