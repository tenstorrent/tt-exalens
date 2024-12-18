# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  graph [ --size=4000000] [ --save-csv==filename ] [ --from-csv=filename ] [ --port=8001 ]  [-d <D>...] <log_names>...

Arguments:
  <log_names>        Address to read from

Options:
  -d <D>        Device ID. Optional and repeatable. Default: current device
  --size=<size>  Size of the buffer to read [default: 4000000]
  --port=<port>  Port to serve the graph [default: 8001]
  --save-csv=<filename>  Save the log data to a CSV file
  --from-csv=<filename>  Read the log data from a CSV file

Description:
  Reads and prints a block of data from address 'addr' at core <core-loc>.

Examples:
  graph current
  graph -d 1 current power
  graph current power --size 10000000
  graph current power --save-csv log_data.csv
"""

command_metadata = {
    "short": "graph",
    "type": "low-level", 
    "description": __doc__,
    "context": ["limited", "metal"],
}

from docopt import docopt
from ttlens.tt_uistate import UIState
from ttlens.tt_lens_context import Context
from typing import List
from ttlens.tt_arc_dbg_fw_log_context import   ArcDfwLogContextFromYaml,ArcDfwLogContextFromList
import os
from ttlens.tt_arc_dbg_fw import ArcDebugLoggerFw

def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(command_metadata["description"], argv=cmd_text.split()[1:])

    log_names = args["<log_names>"]
    size = int(args["--size"]) if args["--size"] else 40000
    port = int(args["--port"]) if args["--port"] else 8001
    save_csv = args["--save-csv"] if args["--save-csv"] else None
    from_csv = args["--from-csv"] if args["--from-csv"] else None

    devices = args["-d"]
    if devices:
        for device_id in devices:
            graph(log_names, size, port, save_csv, from_csv, device_id, context)
    else:
        graph(log_names, size, port, save_csv, from_csv, ui_state.current_device_id, context)

def graph(log_names: List[str], size: int, port: int, save_csv: str, from_csv: str, device_id: int, context: Context):
    TT_METAL_ARC_DEBUG_BUFFER_SIZE=size
    os.environ["TT_METAL_ARC_DEBUG_BUFFER_SIZE"] = str(TT_METAL_ARC_DEBUG_BUFFER_SIZE)
    
    log_data = {}
    if from_csv:
        log_data = ArcDebugLoggerFw.read_log_data_from_csv(from_csv)
    else:
        if log_names[0] == "all":
            log_context = ArcDfwLogContextFromYaml("default")
        else:
            log_context = ArcDfwLogContextFromList(log_names)

        arc_fw = ArcDebugLoggerFw(log_context, device_id= device_id, context=context)
        arc_fw.load()
        log_data = arc_fw.log_until_full_buffer_and_parse_logs()

    if save_csv:
        ArcDebugLoggerFw.save_log_data_to_csv(log_data, save_csv)

    ArcDebugLoggerFw.open_graph_in_a_browser(log_data, log_names, port)
    arc_fw.save_graph_as_picture(log_data,"sefe.png")
