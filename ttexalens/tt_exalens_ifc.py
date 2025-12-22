# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from abc import abstractmethod
import base64
import io
import os
import serpent
import sys
import Pyro5.api

from ttexalens import util as util


ttexalens_pybind_path = util.application_path() + "/lib"
if not os.path.exists(ttexalens_pybind_path):
    ttexalens_pybind_path = util.application_path() + "/../build/lib"
sys.path.append(ttexalens_pybind_path)

try:
    # This is a pybind module so we don't need from .
    from ttexalens_pybind import open_simulation, open_device, TTExaLensImplementation
except ImportError as error:
    if not os.path.isfile(os.path.join(ttexalens_pybind_path, "ttexalens_pybind.so")):
        print(f"Error: 'ttexalens_pybind.so' not found in {ttexalens_pybind_path}. Try: make build")
    else:
        print(f"Error: Failed to import ttexalens_pybind module. Error {error}.")
    sys.exit(1)


class TTExaLensCommunicator(TTExaLensImplementation):
    """
    Base class for the TTExaLens interfaces. It extends binding class with file access methods.
    """

    @abstractmethod
    def get_file(self, file_path: str) -> str:
        pass

    @abstractmethod
    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        pass


class TTExaLensPybind(TTExaLensCommunicator):
    """
    Pybind implementation of the TTExaLens communicator.
    """

    def __init__(
        self,
        wanted_devices: list[int] = [],
        init_jtag=False,
        initialize_with_noc1=False,
        simulation_directory: str | None = None,
    ):
        device: TTExaLensImplementation | None = None
        if simulation_directory:
            device = open_simulation(simulation_directory)
            if device is None:
                raise Exception("Failed to open simulation using pybind library")
        else:
            # Use UMD's existing env var only for debug case, but don't override if user provided it.
            if util.Verbosity.get() == util.Verbosity.DEBUG and "TT_LOGGER_LEVEL" not in os.environ:
                os.environ["TT_LOGGER_LEVEL"] = "debug"
            device = open_device(ttexalens_pybind_path, wanted_devices, init_jtag, initialize_with_noc1)
            if device is None:
                raise Exception("Failed to open device using pybind library")
        self.device: TTExaLensImplementation = device

        # Forward all methods from TTExaLensImplementation to self emulating inheritance
        for attr_name in dir(TTExaLensImplementation):
            if attr_name.startswith("__"):
                continue
            attr = getattr(self.device, attr_name)
            if callable(attr):
                setattr(self, attr_name, attr)

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


def init_pybind(
    wanted_devices=None, init_jtag=False, initialize_with_noc1=False, simulation_directory: str | None = None
):
    if not wanted_devices:
        wanted_devices = []

    communicator = TTExaLensPybind(wanted_devices, init_jtag, initialize_with_noc1, simulation_directory)
    util.VERBOSE("Device opened successfully.")
    return communicator


class TTExaLensClientWrapper:
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


def connect_to_server(server_host="localhost", port=5555) -> TTExaLensCommunicator:
    pyro_address = f"PYRO:communicator@{server_host}:{port}"
    util.VERBOSE(f"Connecting to ttexalens-server at {pyro_address}...")

    try:
        # We are returning a wrapper around the Pyro5 proxy to provide TTExaLensCommunicator-like behavior.
        # Since this is not a direct instance of TTExaLensCommunicator, mypy will warn; hence the ignore.
        proxy = Pyro5.api.Proxy(pyro_address)
        proxy._pyroSerializer = "marshal"
        return TTExaLensClientWrapper(proxy)  # type: ignore
    except:
        raise util.TTFatalException("Failed to connect to TTExaLens server.")
