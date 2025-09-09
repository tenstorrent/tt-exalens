# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import base64
import io
import os
import sys
import Pyro5.api

from ttexalens import util as util
from ttexalens.tt_exalens_ifc_base import TTExaLensCommunicator


ttexalens_pybind_path = util.application_path() + "/../build/lib"
binary_path = util.application_path() + "/../build/bin"
sys.path.append(ttexalens_pybind_path)

try:
    # This is a pybind module so we don't need from .
    import ttexalens_pybind
except ImportError:
    if not os.path.isfile(os.path.join(ttexalens_pybind_path, "ttexalens_pybind.so")):
        print(f"Error: 'ttexalens_pybind.so' not found in {ttexalens_pybind_path}. Try: make build")
        sys.exit(1)


# TODO: Consider moving this to nanobind to avoid wrapping everything into python class
class TTExaLensPybind(TTExaLensCommunicator):
    def __init__(
        self,
        wanted_devices: list = [],
        init_jtag=False,
        initialize_with_noc1=False,
        simulation_directory: str | None = None,
    ):
        super().__init__()
        if simulation_directory:
            if not ttexalens_pybind.open_simulation(simulation_directory):
                raise Exception("Failed to open simulation using pybind library")
        else:
            if not ttexalens_pybind.open_device(binary_path, wanted_devices, init_jtag, initialize_with_noc1):
                raise Exception("Failed to open device using pybind library")

    def _check_result(self, result):
        if result is None:
            raise ttexalens_server_not_supported()
        return result

    def pci_read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self._check_result(ttexalens_pybind.pci_read32(noc_id, chip_id, noc_x, noc_y, address))

    def pci_write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        return self._check_result(ttexalens_pybind.pci_write32(noc_id, chip_id, noc_x, noc_y, address, data))

    def pci_read(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, size: int):
        return self._check_result(ttexalens_pybind.pci_read(noc_id, chip_id, noc_x, noc_y, address, size))

    def pci_write(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes):
        return self._check_result(ttexalens_pybind.pci_write(noc_id, chip_id, noc_x, noc_y, address, data, len(data)))

    def pci_read32_raw(self, chip_id: int, address: int):
        return self._check_result(ttexalens_pybind.pci_read32_raw(chip_id, address))

    def pci_write32_raw(self, chip_id: int, address: int, data: int):
        return self._check_result(ttexalens_pybind.pci_write32_raw(chip_id, address, data))

    def dma_buffer_read32(self, chip_id: int, address: int, channel: int):
        return self._check_result(ttexalens_pybind.dma_buffer_read32(chip_id, address, channel))

    def pci_read_tile(
        self,
        noc_id: int,
        chip_id: int,
        noc_x: int,
        noc_y: int,
        address: int,
        size: int,
        data_format: int,
    ):
        return self._check_result(
            ttexalens_pybind.pci_read_tile(noc_id, chip_id, noc_x, noc_y, address, size, data_format)
        )

    def get_cluster_description(self):
        return self._check_result(ttexalens_pybind.get_cluster_description())

    def convert_from_noc0(self, chip_id, noc_x, noc_y, core_type, coord_system):
        return self._check_result(ttexalens_pybind.convert_from_noc0(chip_id, noc_x, noc_y, core_type, coord_system))

    def get_device_ids(self):
        return self._check_result(ttexalens_pybind.get_device_ids())

    def get_device_arch(self, chip_id: int):
        return self._check_result(ttexalens_pybind.get_device_arch(chip_id))

    def get_device_soc_description(self, chip_id: int):
        return self._check_result(ttexalens_pybind.get_device_soc_description(chip_id))

    def jtag_read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int):
        if address % 4 != 0:
            raise Exception("Unaligned access in jtag_read32")
        return self._check_result(ttexalens_pybind.jtag_read32(noc_id, chip_id, noc_x, noc_y, address))

    def jtag_write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        if address % 4 != 0:
            raise Exception("Unaligned access in jtag_write32")
        return self._check_result(ttexalens_pybind.jtag_write32(noc_id, chip_id, noc_x, noc_y, address, data))

    def jtag_read32_axi(self, chip_id: int, address: int):
        if address % 4 != 0:
            raise Exception("Unaligned access in jtag_read32_axi")
        return self._check_result(ttexalens_pybind.jtag_read32_axi(chip_id, address))

    def jtag_write32_axi(self, chip_id: int, address: int, data: int):
        if address % 4 != 0:
            raise Exception("Unaligned access in jtag_write32_axi")
        return self._check_result(ttexalens_pybind.jtag_write32_axi(chip_id, address, data))

    def get_file(self, file_path: str) -> str:
        content = None
        with open(file_path, "r") as f:
            content = f.read()
        return self._check_result(content)

    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        return open(binary_path, "rb")

    def arc_msg(
        self, noc_id: int, device_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int
    ):
        return self._check_result(
            ttexalens_pybind.arc_msg(noc_id, device_id, msg_code, wait_for_done, arg0, arg1, timeout)
        )

    def read_arc_telemetry_entry(self, device_id, telemetry_tag):
        return self._check_result(ttexalens_pybind.read_arc_telemetry_entry(device_id, telemetry_tag))


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
        return lambda *args, **kwargs: TTExaLensClientWrapper.convert_bytes(function(*args, **kwargs))

    @staticmethod
    def convert_bytes(data):
        if isinstance(data, dict) and data.get("encoding") == "base64" and "data" in data:
            return base64.b64decode(data["data"])
        return data


def connect_to_server(server_host="localhost", port=5555):
    pyro_address = f"PYRO:communicator@{server_host}:{port}"
    util.VERBOSE(f"Connecting to ttexalens-server at {pyro_address}...")

    try:
        return TTExaLensClientWrapper(Pyro5.api.Proxy(pyro_address))
    except:
        raise util.TTFatalException("Failed to connect to TTExaLens server.")
