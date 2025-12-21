# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  gdb start [<port>]
  gdb stop

Options:
  <port>         Port of the GDB server. If not specified, an available port will be chosen.

Description:
  Starts or stops gdb server.

Examples:
  gdb start
  gdb start 6767
  gdb stop
"""

from ttexalens.uistate import UIState
from ttexalens import util as util
from ttexalens.command_parser import CommandMetadata, tt_docopt

command_metadata = CommandMetadata(
    short_name="gdb",
    type="high-level",
    description=__doc__,
    context=["limited", "metal"],
)


def run(cmd_text, context, ui_state: UIState):
    dopt = tt_docopt(command_metadata, cmd_text)
    if dopt.args["start"]:
        if dopt.args["<port>"] is None:
            try:
                ui_state.start_gdb()
            except Exception as e:
                util.ERROR(f"Failed to start GDB server on an available port: {e}")
        else:
            try:
                port = int(dopt.args["<port>"])
                ui_state.start_gdb(port)
            except:
                util.ERROR("Invalid port number")
    elif dopt.args["stop"]:
        ui_state.stop_gdb()
    else:
        util.ERROR("Invalid command")
