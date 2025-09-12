# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import inspect
import threading
import Pyro5.api
from ttexalens import util as util
from ttexalens.tt_exalens_ifc import TTExaLensCommunicator


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

    def wrap_communicator_method(self, method_name: str):
        method = getattr(self.communicator, method_name)
        return Pyro5.api.expose(lambda *args, **kwargs: method(*args, **kwargs))

    def expose_communicator(self):
        # Pyro5 requires methods to be explicitly exposed; we do this dynamically for all methods.
        # This way, users don't need to use @Pyro5.api.expose on every method in TTExaLensCommunicator.
        communicator_type = type(self.communicator)
        for name in dir(communicator_type):
            if name.startswith("_"):
                continue
            thing = getattr(communicator_type, name)
            if inspect.ismethod(thing) or inspect.isfunction(thing):
                setattr(communicator_type, name, Pyro5.api.expose(thing))
            elif callable(thing):
                # This branch is for nanobind methods.
                # As we cannot update the method in place, we create a wrapper function.
                # Performance should not be an issue as we already have networking overhead.
                method = self.wrap_communicator_method(name)
                setattr(communicator_type, name, method)
                setattr(self.communicator, name, method)
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
