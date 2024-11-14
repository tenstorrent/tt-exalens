#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens.tt_debuda_context import Context
from ttlens.tt_gdb_server import GdbServer, ServerSocket
from ttlens.tt_coordinate import OnChipCoordinate

class UIState:
    def __init__(self, context: Context) -> None:
        self.context = context
        self.current_device_id = context.device_ids[0]  # Currently selected device id
        self.current_location = OnChipCoordinate(0, 0, "netlist", self.current_device)  # Currently selected core
        self.current_stream_id = 8  # Currently selected stream_id
        self.current_prompt = ""  # Based on the current x,y,stream_id tuple
        try:
            self.current_graph_name = context.netlist.graphs.first().id()  # Currently selected graph name
        except:
            self.current_graph_name = None
        self.gdb_server: GdbServer = None

    @property
    def current_device(self):
        return self.context.devices[self.current_device_id] if self.current_device_id is not None else None

    def start_gdb(self, port: int):
        if self.gdb_server is not None:
            self.gdb_server.stop()
        server = ServerSocket(port)
        server.start()
        self.gdb_server = GdbServer(self.context, server)
        self.gdb_server.start()

    def stop_gdb(self):
        if self.gdb_server is not None:
            self.gdb_server.stop()
        self.gdb_server = None
