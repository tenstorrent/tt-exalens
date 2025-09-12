# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from abc import abstractmethod
import base64
import io
import os
import sys
import Pyro5.api

from ttexalens import util as util


ttexalens_pybind_path = util.application_path() + "/../build/lib"
binary_path = util.application_path() + "/../build/bin"
sys.path.append(ttexalens_pybind_path)

try:
    # This is a pybind module so we don't need from .
    from ttexalens_pybind import open_simulation, open_device, TTExaLensImplementation
except ImportError:
    if not os.path.isfile(os.path.join(ttexalens_pybind_path, "ttexalens_pybind.so")):
        print(f"Error: 'ttexalens_pybind.so' not found in {ttexalens_pybind_path}. Try: make build")
    else:
        print("Error: Failed to import ttexalens_pybind module. Ensure all dependencies are installed.")
    sys.exit(1)
    ttexalens_pybind = None  # type: ignore


class TTExaLensCommunicator(TTExaLensImplementation):
    @abstractmethod
    def get_file(self, file_path: str) -> str:
        pass

    @abstractmethod
    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        pass


class TTExaLensPybindImplementation(TTExaLensCommunicator):
    def __init__(
        self,
        wanted_devices: list = [],
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
            device = open_device(binary_path, wanted_devices, init_jtag, initialize_with_noc1)
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


def init_pybind(
    wanted_devices=None, init_jtag=False, initialize_with_noc1=False, simulation_directory: str | None = None
):
    if not wanted_devices:
        wanted_devices = []

    communicator = TTExaLensPybindImplementation(wanted_devices, init_jtag, initialize_with_noc1, simulation_directory)
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
        return lambda *args, **kwargs: TTExaLensClientWrapper.convert_bytes(function(*args, **kwargs))

    @staticmethod
    def convert_bytes(data):
        if isinstance(data, dict) and data.get("encoding") == "base64" and "data" in data:
            return base64.b64decode(data["data"])
        return data


def connect_to_server(server_host="localhost", port=5555) -> TTExaLensCommunicator:
    pyro_address = f"PYRO:communicator@{server_host}:{port}"
    util.VERBOSE(f"Connecting to ttexalens-server at {pyro_address}...")

    try:
        # We are returning a wrapper around the Pyro5 proxy to provide TTExaLensCommunicator-like behavior.
        # Since this is not a direct instance of TTExaLensCommunicator, mypy will warn; hence the ignore.
        return TTExaLensClientWrapper(Pyro5.api.Proxy(pyro_address))  # type: ignore
    except:
        raise util.TTFatalException("Failed to connect to TTExaLens server.")
