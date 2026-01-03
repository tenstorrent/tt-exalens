# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
import io
import Pyro5.api
import Pyro5.configure
import serpent
import threading
from typing import TYPE_CHECKING
from ttexalens import util as util
import tt_umd

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
        self.umd_registered_objects: dict[int, tuple[object, object]] = {}
        self.umd_registered_objects_lock = threading.Lock()

    def start(self):
        if self.daemon or self.thread:
            raise util.TTFatalException("Server already started")
        self.daemon = Pyro5.api.Daemon(port=self.port)
        umd_wrapper = self._wrap_object(self.umd_api)
        self.umd_registered_objects[id(self.umd_api)] = (self.umd_api, None)
        self.daemon.register(umd_wrapper, objectId="umd_api")
        self.daemon.register(self.file_api, objectId="file_api")
        self.thread = threading.Thread(target=self.daemon.requestLoop, daemon=True)
        self.thread.start()

    def stop(self):
        if self.daemon:
            self.daemon.unregister(self.file_api)
            with self.umd_registered_objects_lock:
                for obj in self.umd_registered_objects.values():
                    self.daemon.unregister(obj[0])
                self.umd_registered_objects.clear()
            self.daemon.shutdown()
        if self.thread:
            self.thread.join()
        self.daemon = None
        self.thread = None

    def _wrap_object(self, obj: object):
        @Pyro5.api.expose
        class UmdApiWrapper:
            def __init__(self, server: TTExaLensServer):
                self.server = server

            def _create_umd_method_wrapper(self, method):
                def wrapper_method(*args, **kwargs):
                    result = method(*args, **kwargs)
                    result_type = type(result)
                    # Check if result_type is simple type
                    if result_type in (int, float, str, bool, type(None), list, dict, set, tuple, bytes):
                        return result
                    # Check if result_type is in known serializable types
                    global UMD_SERIALIZABLE_TYPES
                    if result_type in UMD_SERIALIZABLE_TYPES:
                        return result
                    # For complex types, register them and return a proxy
                    with self.server.umd_registered_objects_lock:
                        object_id = id(result)
                        if object_id not in self.server.umd_registered_objects:
                            assert self.server.daemon is not None
                            wrapped_result = self.server._wrap_object(result)
                            self.server.daemon.register(wrapped_result, objectId=f"umd_obj_{object_id}")
                            proxy = Pyro5.api.Proxy(f"PYRO:umd_obj_{object_id}@localhost:{self.server.port}")
                            proxy._pyroSerializer = "serpent"
                            self.server.umd_registered_objects[object_id] = (wrapped_result, proxy)
                        return self.server.umd_registered_objects[object_id][1]

                return wrapper_method

        wrapper = UmdApiWrapper(self)
        wrapper_type = type(wrapper)
        for method_name in dir(obj):
            if method_name.startswith("_"):
                continue
            method = getattr(obj, method_name)
            if callable(method):
                new_method = Pyro5.api.expose(wrapper._create_umd_method_wrapper(method))
                setattr(wrapper, method_name, new_method)
                setattr(wrapper_type, method_name, new_method)
        return wrapper


UMD_SERIALIZABLE_TYPES = {
    tt_umd.ARCH,
    tt_umd.IODeviceType,
    tt_umd.CoreType,
    tt_umd.CoordSystem,
    tt_umd.CoreCoord,
}


def umd_type_to_dict(obj):
    if isinstance(obj, tt_umd.ARCH):
        return {"__class__": "tt_umd.ARCH", "value": obj.name}
    if isinstance(obj, tt_umd.IODeviceType):
        return {"__class__": "tt_umd.IODeviceType", "value": obj.name}
    if isinstance(obj, tt_umd.CoreType):
        return {"__class__": "tt_umd.CoreType", "value": obj.name}
    if isinstance(obj, tt_umd.CoordSystem):
        return {"__class__": "tt_umd.CoordSystem", "value": obj.name}
    if isinstance(obj, tt_umd.CoreCoord):
        return {
            "__class__": "tt_umd.CoreCoord",
            "x": obj.x,
            "y": obj.y,
            "core_type": obj.core_type.name,
            "coord_system": obj.coord_system.name,
        }
    raise TypeError(f"Cannot serialize type {type(obj)}")


def umd_type_from_dict(cls, data):
    if cls == "tt_umd.ARCH":
        return tt_umd.ARCH[data["value"]]
    if cls == "tt_umd.IODeviceType":
        return tt_umd.IODeviceType[data["value"]]
    if cls == "tt_umd.CoreType":
        return tt_umd.CoreType[data["value"]]
    if cls == "tt_umd.CoordSystem":
        return tt_umd.CoordSystem[data["value"]]
    if cls == "tt_umd.CoreCoord":
        coord_system = tt_umd.CoordSystem[data["coord_system"]]
        core_type = tt_umd.CoreType[data["core_type"]]
        x = data["x"]
        y = data["y"]
        return tt_umd.CoreCoord(x, y, core_type, coord_system)
    return data


import enum

Pyro5.api.register_class_to_dict(enum.Enum, umd_type_to_dict)
for tt_umd_type in UMD_SERIALIZABLE_TYPES:
    Pyro5.api.register_class_to_dict(tt_umd_type, umd_type_to_dict)
    Pyro5.api.register_dict_to_class(f"tt_umd.{tt_umd_type.__name__}", umd_type_from_dict)
Pyro5.configure.global_config.SERPENT_BYTES_REPR = True


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
        proxy._pyroSerializer = "serpent"
        umd_api: UmdApi = proxy  # type: ignore

        # Connect to FileAccessApi
        pyro_file_api_address = f"PYRO:file_api@{server_host}:{port}"
        util.VERBOSE(f"Connecting FileAccess API to ttexalens-server at {pyro_file_api_address}...")

        # We are returning a wrapper around the Pyro5 proxy to provide FileAccessApi-like behavior.
        # Since this is not a direct instance of FileAccessApi, mypy will warn; hence the ignore.
        proxy = Pyro5.api.Proxy(pyro_file_api_address)
        proxy._pyroSerializer = "serpent"
        file_api: FileAccessApi = FileAccessApiWrapper(proxy)  # type: ignore

        # Return connected APIs
        return umd_api, file_api
    except:
        raise util.TTFatalException("Failed to connect to TTExaLens server.")
