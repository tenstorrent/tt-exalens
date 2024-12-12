# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
"""
Usage:
  graph [-d <D>...] <log_names>...

Arguments:
  <log_names>        Address to read from

Options:
  -d <D>        Device ID. Optional and repeatable. Default: current device

Description:
  Reads and prints a block of data from address 'addr' at core <core-loc>.

Examples:
  graph current
  graph -d 1 current power
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
from ttlens.tt_arc_dbg_fw_graph import arc_dfw_get_logs

import plotly.express as px
from http.server import HTTPServer, SimpleHTTPRequestHandler
from ttlens.tt_arc_dbg_fw_log_context import  LogInfo, ArcDfwLogContext, ArcDfwLogContextFromYaml,ArcDfwLogContextFromList
import threading
import os
import socket

def run(cmd_text, context, ui_state: UIState = None):
    args = docopt(command_metadata["description"], argv=cmd_text.split()[1:])

    log_names = args["<log_names>"]

    devices = args["-d"]
    if devices:
        for device_id in devices:
            graph(log_names,device_id, context)
    else:
        graph(log_names, ui_state.current_device_id, context)

def graph(log_names: List[str], device_id: int, context: Context):


    TT_METAL_ARC_DEBUG_BUFFER_SIZE=1024*64    
    os.environ["TT_METAL_ARC_DEBUG_BUFFER_SIZE"] = str(TT_METAL_ARC_DEBUG_BUFFER_SIZE)
    
    log_context = ArcDfwLogContextFromList(log_names)
    buffer_data = arc_dfw_get_logs(log_context, device_id, context)

    figures = {}
    for key, data in buffer_data.items():
        figures[key] = px.line(x=range(len(data)), y=data, title=key.capitalize())

    combined_html = "combined_plots.html"
    with open(combined_html, "w") as f:
        f.write("<html><head><title>Combined Plots</title></head><body>\n")
        for key, fig in figures.items():
            f.write(f"<h1>{key.capitalize()}</h1>\n")
            f.write(fig.to_html(full_html=False, include_plotlyjs='cdn' if key == list(figures.keys())[0] else False))
        f.write("</body></html>")
    
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    httpd = None
    
    def serve_html():
        nonlocal httpd
        port = 8001
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

