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


try:
    import datetime
    import tempfile
    from typing import Sequence
    import tt_umd
    from ttexalens.umd_device_wrapper import UmdDeviceWrapper

    class TTExaLensUmdImplementation(TTExaLensCommunicator):
        def __init__(
            self,
            wanted_devices: list = [],
            init_jtag=False,
            initialize_with_noc1=False,
            simulation_directory: str | None = None,
        ):
            self.temp_working_directory = tempfile.mkdtemp(prefix="ttexalens_server_XXXXXX")

            # // Disable UMD logging
            # tt::umd::logging::set_level(tt::umd::logging::level::error);

            # TODO: Hack on UMD on how to use/initialize with noc1. This should be removed once we have a proper way to use noc1
            tt_umd.TTDevice.use_noc1(initialize_with_noc1)

            device_type = tt_umd.IODeviceType.PCIe if not init_jtag else tt_umd.IODeviceType.JTAG
            self.cluster_descriptor, self.devices = tt_umd.TopologyDiscovery.discover()

            if len(self.cluster_descriptor.get_all_chips()) == 0:
                raise RuntimeError("No Tenstorrent devices were detected on this system.")

            self.cluster_descriptor_path = os.path.join(self.temp_working_directory, "cluster_desc.yaml")
            self.device_soc_descriptors_yamls: dict[int, str] = {}
            self.devices: dict[int, UmdDeviceWrapper] = {}
            self.device_ids: list[int] = []

            # Setup used devices
            self.device_ids = []
            target_devices = set()

            for i in self.cluster_descriptor.get_all_chips():
                self.device_ids.append(i)

            self.device_id_to_unique_id = {}
            unique_ids = self.cluster_descriptor.get_chip_unique_ids()
            for device_id in self.device_ids:
                if device_id in unique_ids:
                    self.device_id_to_unique_id[device_id] = unique_ids[device_id]

            # If we specified which devices we want, check that they are available and then extract their ids
            if len(wanted_devices) > 0:
                for wanted_device in wanted_devices:
                    if wanted_device not in self.device_ids:
                        raise RuntimeError(f"Device {wanted_device} is not available.")
                self.device_ids = wanted_devices

            for device_id in self.device_ids:
                target_devices.add(device_id)
            self.soc_descriptors = {}
            self.device_soc_descriptors_yamls = {}
            self.cached_arc_telemetry_readers = {}
            for chip_id, device in self.devices.items():

                soc_descriptor = tt_umd.SocDescriptor(device)
                file_name = os.path.join(self.temp_working_directory, f"device_desc_runtime_{chip_id}.yaml")
                wrapped_device.soc_descriptor.serialize_to_file(file_name)
                self.device_soc_descriptors_yamls[chip_id] = file_name

        def __get_device(self, chip_id: int) -> UmdDeviceWrapper:
            if chip_id not in self.devices:
                raise RuntimeError(f"Device with chip id {chip_id} not found.")
            return self.devices[chip_id]

        def read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int) -> int:
            return self.__get_device(chip_id).read32(noc_id, noc_x, noc_y, address)

        def write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int) -> int:
            return self.__get_device(chip_id).write32(noc_id, noc_x, noc_y, address, data)

        def read(
            self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, size: int, use_4B_mode: bool
        ) -> bytes:
            return self.__get_device(chip_id).read(noc_id, noc_x, noc_y, address, size, use_4B_mode)

        def write(
            self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes, use_4B_mode: bool
        ) -> int:
            return self.__get_device(chip_id).write(noc_id, noc_x, noc_y, address, data, use_4B_mode)

        def pci_read32_raw(self, chip_id: int, address: int) -> int:
            return self.__get_device(chip_id).pci_read32_raw(address)

        def pci_write32_raw(self, chip_id: int, address: int, data: int) -> int:
            return self.__get_device(chip_id).pci_write32_raw(address, data)

        def dma_buffer_read32(self, chip_id: int, address: int, channel: int) -> int:
            return self.__get_device(chip_id).dma_buffer_read32(address, channel)

        def pci_read_tile(
            self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, size: int, data_format: int
        ) -> str:
            return self.__get_device(chip_id).pci_read_tile(noc_id, noc_x, noc_y, address, size, data_format)

        def get_cluster_description(self):
            return self.cluster_descriptor_path

        def get_device_ids(self):
            return self.device_ids

        def get_device_arch(self, chip_id: int) -> str:
            return str(self.__get_device(chip_id).arch)

        def get_device_soc_description(self, chip_id: int) -> str:
            return self.device_soc_descriptors_yamls[chip_id]

        def convert_from_noc0(self, chip_id: int, noc_x: int, noc_y: int, core_type: str, coord_system: str):
            return self.__get_device(chip_id).convert_from_noc0(noc_x, noc_y, core_type, coord_system)

        def arc_msg(
            self,
            noc_id: int,
            chip_id: int,
            msg_code: int,
            wait_for_done: bool,
            args: Sequence[int],
            timeout: datetime.timedelta | float,
        ):
            return self.__get_device(chip_id).arc_msg(noc_id, msg_code, wait_for_done, args, timeout)

        def read_arc_telemetry_entry(self, chip_id: int, telemetry_tag: int) -> int:
            return self.__get_device(chip_id).read_arc_telemetry_entry(telemetry_tag)

        def get_firmware_version(self, chip_id: int) -> tuple[int, int, int]:
            return self.__get_device(chip_id).get_firmware_version()

        def warm_reset(self, is_galaxy_configuration: bool = False) -> None:
            if is_galaxy_configuration:
                tt_umd.WarmReset.ubb_warm_reset()
            else:
                tt_umd.WarmReset.warm_reset()

        def get_remote_transfer_eth_core(self, chip_id: int) -> tuple[int, int] | None:
            return self.__get_device(chip_id).get_remote_transfer_eth_core()

        def get_device_unique_id(self, chip_id: int) -> int:
            return self.__get_device(chip_id).unique_id

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

except:
    print("Error: Failed to import tt_umd module.")
    TTExaLensUmdImplementation = TTExaLensPybind  # type: ignore


def init_pybind(
    wanted_devices=None, init_jtag=False, initialize_with_noc1=False, simulation_directory: str | None = None
):
    if not wanted_devices:
        wanted_devices = []

    if "TT_LOGGER_LEVEL" not in os.environ:
        if util.Verbosity.get() == util.Verbosity.DEBUG:
            os.environ["TT_LOGGER_LEVEL"] = "debug"
        elif util.Verbosity.get() == util.Verbosity.TRACE:
            os.environ["TT_LOGGER_LEVEL"] = "trace"

    communicator = TTExaLensUmdImplementation(wanted_devices, init_jtag, initialize_with_noc1, simulation_directory)
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
