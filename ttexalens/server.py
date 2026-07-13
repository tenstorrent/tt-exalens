# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from dataclasses import dataclass
import inspect
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
    def is_local(self) -> bool:
        return True

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
    @dataclass
    class UmdRegisteredObject:
        pyro5_id: str
        wrapped_object: object
        proxy: object | None = None

    def __init__(self, port: int, umd_api: UmdApi, file_api: FileAccessApi):
        self.port = port
        self.umd_api = umd_api
        self.file_api = file_api
        self.daemon: Pyro5.api.Daemon | None = None
        self.thread: threading.Thread | None = None
        self.umd_registered_objects: dict[int, TTExaLensServer.UmdRegisteredObject] = {}
        self.umd_registered_objects_lock = threading.Lock()
        self._wrapper_classes: dict[type, type] = {}

    def start(self):
        if self.daemon or self.thread:
            raise util.TTFatalException("Server already started")
        self.daemon = Pyro5.api.Daemon(port=self.port)
        umd_wrapper = self._wrap_object(self.umd_api)
        self.umd_registered_objects[id(self.umd_api)] = TTExaLensServer.UmdRegisteredObject("umd_api", self.umd_api)
        self.daemon.register(umd_wrapper, objectId="umd_api")
        self.daemon.register(self.file_api, objectId="file_api")
        self.thread = threading.Thread(target=self.daemon.requestLoop, daemon=True)
        self.thread.start()

    def stop(self):
        if self.daemon:
            self.daemon.unregister(self.file_api)
            with self.umd_registered_objects_lock:
                for obj in self.umd_registered_objects.values():
                    self.daemon.unregister(obj.pyro5_id)
                self.umd_registered_objects.clear()
            self.daemon.shutdown()
        if self.thread:
            self.thread.join()
        self.daemon = None
        self.thread = None

    def _wrap_result(self, result):
        """Prepares a method/property result for transport over Pyro5.

        Native types and known serializable types are returned as-is so Pyro5/serpent
        forwards them directly. Any other object is wrapped, registered with the daemon
        (once per object), and returned as a proxy.
        """
        global SIMPLE_TYPES, UMD_SERIALIZABLE_TYPES

        result_type = type(result)
        # Check if result_type is simple type
        if result_type in SIMPLE_TYPES:
            return result
        # Check if result_type is in known serializable types
        if result_type in UMD_SERIALIZABLE_TYPES:
            return result
        # For complex types, register them and return a proxy
        with self.umd_registered_objects_lock:
            object_id = id(result)
            if object_id not in self.umd_registered_objects:
                assert self.daemon is not None
                wrapped_result = self._wrap_object(result)
                pyro5_id = f"umd_obj_{object_id}"
                self.daemon.register(wrapped_result, objectId=pyro5_id)
                proxy = Pyro5.api.Proxy(f"PYRO:{pyro5_id}@localhost:{self.port}")
                proxy._pyroSerializer = "serpent"
                self.umd_registered_objects[object_id] = TTExaLensServer.UmdRegisteredObject(
                    pyro5_id, wrapped_result, proxy
                )
            return self.umd_registered_objects[object_id].proxy

    def _wrap_object(self, obj: object):
        """Wraps an object so its public API can be exposed over Pyro5.

        The wrapper *type* is built once per wrapped object type and cached; each object of
        that type is then wrapped by simply constructing the cached wrapper class around it.
        """
        wrapper_class = self._get_wrapper_class(type(obj))
        return wrapper_class(obj, self)

    def _get_wrapper_class(self, obj_type: type) -> type:
        cached = self._wrapper_classes.get(obj_type)
        if cached is not None:
            return cached

        @Pyro5.api.expose
        class UmdApiWrapper:
            def __init__(self, obj, server: TTExaLensServer):
                self.obj = obj
                self.server = server

        def create_method_wrapper(method_name: str | None = None, fget=None, fset=None):
            def wrapper_method(self, *args, **kwargs):
                if fget is not None:
                    result = fget(self.obj)
                elif fset is not None:
                    return fset(self.obj, *args, **kwargs)
                else:
                    assert method_name is not None
                    result = getattr(self.obj, method_name)(*args, **kwargs)
                return self.server._wrap_result(result)

            return wrapper_method

        for method_name in obj_type.__dict__:
            if method_name.startswith("_"):
                continue
            attribute = getattr(obj_type, method_name)
            if inspect.isdatadescriptor(attribute):
                getter = None
                setter = None
                if getattr(attribute, "fset", None):
                    setter = Pyro5.api.expose(create_method_wrapper(fset=attribute.fset))  # type: ignore
                if getattr(attribute, "fget", None):
                    getter = Pyro5.api.expose(create_method_wrapper(fget=attribute.fget))  # type: ignore
                new_property = property(getter, setter)  # pyright: ignore[reportArgumentType]
                setattr(UmdApiWrapper, method_name, new_property)
            elif callable(attribute):
                new_method = Pyro5.api.expose(create_method_wrapper(method_name=method_name))
                setattr(UmdApiWrapper, method_name, new_method)

        self._wrapper_classes[obj_type] = UmdApiWrapper
        return UmdApiWrapper


SIMPLE_TYPES = (int, float, str, bool, type(None), list, dict, set, tuple, bytes)
UMD_SERIALIZABLE_TYPES = {
    tt_umd.ARCH,
    tt_umd.BoardType,
    tt_umd.IODeviceType,
    tt_umd.CoreType,
    tt_umd.CoordSystem,
    tt_umd.tt_xy_pair,
    tt_umd.CoreCoord,
    tt_umd.SemVer,
    tt_umd.FirmwareBundleVersion,
    tt_umd.TelemetryTag,
    tt_umd.DramTrainingStatus,
    tt_umd.NocId,
}
UMD_SERIALIZABLE_TYPES_NAMES: dict[str, type] = {f"{t.__module__}.{t.__name__}": t for t in UMD_SERIALIZABLE_TYPES}


def umd_type_to_dict(obj):
    if isinstance(obj, enum.Enum):
        return {"__class__": f"{obj.__class__.__module__}.{obj.__class__.__name__}", "value": obj.name}
    if isinstance(obj, tt_umd.CoreCoord):
        return {
            "__class__": "tt_umd.tt_umd.CoreCoord",
            "x": obj.x,
            "y": obj.y,
            "core_type": obj.core_type.name,
            "coord_system": obj.coord_system.name,
        }
    if isinstance(obj, tt_umd.tt_xy_pair):
        return {
            "__class__": "tt_umd.tt_umd.tt_xy_pair",
            "x": obj.x,
            "y": obj.y,
        }
    if isinstance(obj, tt_umd.SemVer):
        return {
            "__class__": "tt_umd.tt_umd.SemVer",
            "major": obj.major,
            "minor": obj.minor,
            "patch": obj.patch,
        }
    if isinstance(obj, tt_umd.FirmwareBundleVersion):
        return {
            "__class__": "tt_umd.tt_umd.FirmwareBundleVersion",
            "major": obj.major,
            "minor": obj.minor,
            "patch": obj.patch,
        }
    raise TypeError(f"Cannot serialize type {type(obj)}")


def umd_type_from_dict(cls, data):
    type = UMD_SERIALIZABLE_TYPES_NAMES.get(cls, None)
    if type is not None:
        if issubclass(type, enum.Enum):
            return type[data["value"]]
        if type == tt_umd.CoreCoord:
            coord_system = tt_umd.CoordSystem[data["coord_system"]]
            core_type = tt_umd.CoreType[data["core_type"]]
            x = data["x"]
            y = data["y"]
            return tt_umd.CoreCoord(x, y, core_type, coord_system)
        if type == tt_umd.tt_xy_pair:
            x = data["x"]
            y = data["y"]
            return tt_umd.tt_xy_pair(x, y)
        if type == tt_umd.SemVer:
            major = data["major"]
            minor = data["minor"]
            patch = data["patch"]
            return tt_umd.SemVer(major, minor, patch)
        if type == tt_umd.FirmwareBundleVersion:
            major = data["major"]
            minor = data["minor"]
            patch = data["patch"]
            return tt_umd.FirmwareBundleVersion(major, minor, patch)
    return data


import enum

Pyro5.api.register_class_to_dict(enum.Enum, umd_type_to_dict)
for tt_umd_type in UMD_SERIALIZABLE_TYPES:
    Pyro5.api.register_class_to_dict(tt_umd_type, umd_type_to_dict)
    Pyro5.api.register_dict_to_class(f"{tt_umd_type.__module__}.{tt_umd_type.__name__}", umd_type_from_dict)
Pyro5.configure.global_config.SERPENT_BYTES_REPR = True  # pyright: ignore[reportAttributeAccessIssue]


def start_server(port: int, context: Context):
    try:
        server = TTExaLensServer(port, context.umd_api, context.file_api)
        server.start()
        util.INFO(f"ttexalens-server listening on port {port}")
        return server
    except Exception as e:
        print(f"Error starting ttexalens-server: {e}")
        raise util.TTFatalException("Could not start ttexalens-server.")


class RemoteUmdDevice:
    """
    Client-side adapter around a Pyro5 UmdDevice proxy.
    """

    def __init__(self, proxy):
        self._proxy = proxy

    def noc_read(
        self,
        noc_id: tt_umd.NocId,
        noc0_x: int,
        noc0_y: int,
        address: int,
        buffer: bytearray | memoryview,
        dma_threshold: int,
    ) -> None:
        data = self._proxy.noc_read_bytes(noc_id, noc0_x, noc0_y, address, len(buffer), dma_threshold)
        # Pyro5/serpent returns bytes either as real bytes or as a base64-encoded dict.
        buffer[:] = serpent.tobytes(data) if isinstance(data, dict) else data

    def __getattr__(self, name):
        return getattr(self._proxy, name)


class RemoteUmdApiWrapper:
    """
    Client-side adapter around a Pyro5 UmdApi proxy.
    """

    def __init__(self, proxy):
        self._proxy = proxy

    def get_device(self, chip_id: int) -> RemoteUmdDevice:
        return RemoteUmdDevice(self._proxy.get_device(chip_id))

    def __getattr__(self, name):
        return getattr(self._proxy, name)


class FileAccessApiWrapper:
    """
    A wrapper around the Pyro5 proxy to convert base64-encoded bytes back to bytes.
    """

    def __init__(self, proxy):
        self.proxy = proxy

    def __getattr__(self, name):
        function = getattr(self.proxy, name)
        return lambda *args, **kwargs: function(*args, **kwargs)

    def is_local(self) -> bool:
        return False

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
        if util.VERBOSE_ENABLED:
            util.VERBOSE(f"Connecting UMD API to ttexalens-server at {pyro_umd_api_address}...")
        # We are returning a wrapper around the Pyro5 proxy to provide UmdApi-like behavior.
        proxy = Pyro5.api.Proxy(pyro_umd_api_address)
        proxy._pyroSerializer = "serpent"
        umd_api: UmdApi = RemoteUmdApiWrapper(proxy)  # type: ignore

        # Connect to FileAccessApi
        pyro_file_api_address = f"PYRO:file_api@{server_host}:{port}"
        if util.VERBOSE_ENABLED:
            util.VERBOSE(f"Connecting FileAccess API to ttexalens-server at {pyro_file_api_address}...")

        # We are returning a wrapper around the Pyro5 proxy to provide FileAccessApi-like behavior.
        # Since this is not a direct instance of FileAccessApi, mypy will warn; hence the ignore.
        proxy = Pyro5.api.Proxy(pyro_file_api_address)
        proxy._pyroSerializer = "serpent"
        file_api: FileAccessApi = FileAccessApiWrapper(proxy)  # type: ignore

        # Return connected APIs
        return umd_api, file_api
    except Exception as e:
        raise util.TTFatalException("Failed to connect to TTExaLens server.") from e
