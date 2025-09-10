# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import inspect
import threading
import Pyro5.api
from ttexalens import util as util
from ttexalens.tt_exalens_ifc_base import TTExaLensCommunicator


class TTExaLensServer:
    def __init__(self, port: int, communicator: TTExaLensCommunicator):
        self.port = port
        self.communicator = communicator
        self.daemon: Pyro5.api.Daemon | None = None
        self.thread: threading.Thread | None = None

    def start(self):
        if self.daemon or self.thread:
            raise util.TTFatalException("Server already started")
        self.daemon = Pyro5.api.Daemon(port=self.port)
        self.daemon.register(self.expose_communicator(), objectId="communicator")
        self.thread = threading.Thread(target=self.daemon.requestLoop, daemon=True)
        self.thread.start()

    def stop(self):
        if self.daemon:
            self.daemon.shutdown()
        if self.thread:
            self.thread.join()
        self.daemon = None
        self.thread = None

    def expose_communicator(self):
        communicator_type = type(self.communicator)
        for name in communicator_type.__dict__:
            if name.startswith("_"):
                continue
            thing = getattr(communicator_type, name)
            if inspect.ismethod(thing) or inspect.isfunction(thing):
                setattr(communicator_type, name, Pyro5.api.expose(thing))
        return self.communicator


def start_server(port: int, communicator: TTExaLensCommunicator):
    try:
        server = TTExaLensServer(port, communicator)
        server.start()
        util.INFO(f"ttexalens-server listening on port {port}")
        return server
    except Exception as e:
        print(f"Error starting ttexalens-server: {e}")
        raise util.TTFatalException("Could not start ttexalens-server.")
