# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import io
import Pyro5.api
import serpent
import threading
from typing import TYPE_CHECKING
from ttexalens import util as util

if TYPE_CHECKING:
    from ttexalens.context import Context
    from ttexalens.umd_api import UmdApi


@Pyro5.api.expose
class FileAccessApi:
    def get_file(self, file_path: str) -> str:
        with open(file_path, "r") as f:
            return f.read()

    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        return open(binary_path, "rb")

    def get_binary_content(self, binary_path: str) -> bytes:
        """
        Returns binary file content as base64-encoded data for remote access.
        This method is used by the server to serialize binary data properly.
        """
        with open(binary_path, "rb") as f:
            return f.read()


class TTExaLensServer:
    def __init__(self, port: int, umd_api: UmdApi, file_api: FileAccessApi):
        self.port = port
        self.umd_api = umd_api
        self.file_api = file_api
        self.daemon: Pyro5.api.Daemon | None = None
        self.thread: threading.Thread | None = None

    def start(self):
        if self.daemon or self.thread:
            raise util.TTFatalException("Server already started")
        self.daemon = Pyro5.api.Daemon(port=self.port)
        self.daemon.register(self.umd_api, objectId="umd_api")
        self.daemon.register(self.file_api, objectId="file_api")
        self.thread = threading.Thread(target=self.daemon.requestLoop, daemon=True)
        self.thread.start()

    def stop(self):
        if self.daemon:
            self.daemon.unregister(self.umd_api)
            self.daemon.unregister(self.file_api)
            self.daemon.shutdown()
        if self.thread:
            self.thread.join()
        self.daemon = None
        self.thread = None


def start_server(port: int, context: Context):
    try:
        server = TTExaLensServer(port, context.umd_api, context.file_api)
        server.start()
        util.INFO(f"ttexalens-server listening on port {port}")
        return server
    except Exception as e:
        print(f"Error starting ttexalens-server: {e}")
        raise util.TTFatalException("Could not start ttexalens-server.")


class FileAccessApiWrapper:
    """
    A wrapper around the Pyro5 proxy to convert base64-encoded bytes back to bytes.
    """

    def __init__(self, proxy):
        self.proxy = proxy

    def __getattr__(self, name):
        function = getattr(self.proxy, name)
        return lambda *args, **kwargs: function(*args, **kwargs)

    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        """
        Handle get_binary by calling get_binary_content and wrapping result in BytesIO.
        """
        # Try to call get_binary_content which returns serializable data
        data = self.proxy.get_binary_content(binary_path)
        binary_data = serpent.tobytes(data)
        return io.BytesIO(binary_data)


def connect_to_server(server_host="localhost", port=5555) -> tuple[UmdApi, FileAccessApi]:
    try:
        # Connect to UmdApi
        pyro_umd_api_address = f"PYRO:umd_api@{server_host}:{port}"
        util.VERBOSE(f"Connecting UMD API to ttexalens-server at {pyro_umd_api_address}...")
        # We are returning a wrapper around the Pyro5 proxy to provide UmdApi-like behavior.
        proxy = Pyro5.api.Proxy(pyro_umd_api_address)
        proxy._pyroSerializer = "marshal"
        umd_api: UmdApi = proxy  # type: ignore

        # Connect to FileAccessApi
        pyro_file_api_address = f"PYRO:file_api@{server_host}:{port}"
        util.VERBOSE(f"Connecting FileAccess API to ttexalens-server at {pyro_file_api_address}...")

        # We are returning a wrapper around the Pyro5 proxy to provide FileAccessApi-like behavior.
        # Since this is not a direct instance of FileAccessApi, mypy will warn; hence the ignore.
        proxy = Pyro5.api.Proxy(pyro_file_api_address)
        proxy._pyroSerializer = "marshal"
        file_api: FileAccessApi = FileAccessApiWrapper(proxy)  # type: ignore

        # Return connected APIs
        return umd_api, file_api
    except:
        raise util.TTFatalException("Failed to connect to TTExaLens server.")
