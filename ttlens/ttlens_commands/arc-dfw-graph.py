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
from ttlens.tt_arc_dbg_fw_graph import arc_dfw_get_logs, save_to_csv, read_logs_from_csv

import plotly.express as px
from http.server import HTTPServer, SimpleHTTPRequestHandler
from ttlens.tt_arc_dbg_fw_log_context import  LogInfo, ArcDfwLogContext, ArcDfwLogContextFromYaml,ArcDfwLogContextFromList
import threading
import os
import socket
from ttlens.tt_arc_dbg_fw import read_arc_dfw_buffer 

def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(command_metadata["description"], argv=cmd_text.split()[1:])

    log_names = args["<log_names>"]
    size = int(args["--size"]) if args["--size"] else 4000000
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

    buffer_data = {}
    if from_csv:
        buffer_data = read_logs_from_csv(from_csv)
    else:
        if log_names[0] == "all":
            log_context = ArcDfwLogContextFromYaml("default")
        else:
            log_context = ArcDfwLogContextFromList(log_names)
        buffer_data = arc_dfw_get_logs(log_context, device_id, context)

    if save_csv:
        save_to_csv(buffer_data, save_csv)

    figures = {}
    for key, data in buffer_data.items():
        if key== "heartbeat" and "heartbeat" not in log_names:
            continue
            
        figures[key] = px.line(x=range(len(data)), y=data, title=key.capitalize())

    combined_html = "combined_plots.html"
    with open(combined_html, "w") as f:
        f.write("<html><head><title>Combined Plots</title></head><body>\n")
        for key, fig in figures.items():
            f.write(f"<h1>{key.capitalize()}</h1>\n")
            f.write(fig.to_html(full_html=False, include_plotlyjs='cdn' if key == list(figures.keys())[0] else False))
        f.write("</body></html>")
    
    httpd = None
    
    def serve_html():
        nonlocal httpd
        os.chdir(".")  # Set the directory for the HTTP server
        httpd = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
        print(f"Graph address http://localhost:{port}/{combined_html} if port forwarding is set up.")
        httpd.serve_forever()

    
    thread = threading.Thread(target=serve_html, daemon=True)
    thread.start()

    print("Press Enter to stop the server.")
    input()
    print("Server stopped.")
    if httpd:
        httpd.shutdown()
    thread.join()

