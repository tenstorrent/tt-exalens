# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import threading
import Pyro5.api
from ttexalens import util as util
from ttexalens.tt_exalens_ifc import TTExaLensUmdImplementation


class TTExaLensServer:
    def __init__(self, port: int, communicator: TTExaLensUmdImplementation):
        self.port = port
        self.communicator = communicator
        self.daemon: Pyro5.api.Daemon | None = None
        self.thread: threading.Thread | None = None

    def start(self):
        if self.daemon or self.thread:
            raise util.TTFatalException("Server already started")
        self.daemon = Pyro5.api.Daemon(port=self.port)
        self.daemon.register(self.communicator, objectId="communicator")
        self.thread = threading.Thread(target=self.daemon.requestLoop, daemon=True)
        self.thread.start()

    def stop(self):
        if self.daemon:
            self.daemon.unregister(self.communicator)
            self.daemon.shutdown()
        if self.thread:
            self.thread.join()
        self.daemon = None
        self.thread = None


def start_server(port: int, communicator: TTExaLensUmdImplementation):
    try:
        server = TTExaLensServer(port, communicator)
        server.start()
        util.INFO(f"ttexalens-server listening on port {port}")
        return server
    except Exception as e:
        print(f"Error starting ttexalens-server: {e}")
        raise util.TTFatalException("Could not start ttexalens-server.")
