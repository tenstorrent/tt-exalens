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
    import tt_umd
    import tempfile

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
            self.cluster_descriptor.serialize_to_file(self.cluster_descriptor_path)

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

                soc_descriptor.serialize_to_file(file_name)
                self.device_soc_descriptors_yamls[chip_id] = file_name
                self.soc_descriptors[chip_id] = soc_descriptor

                self.cached_arc_telemetry_readers[chip_id] = None

        def get_device(self, chip_id: int) -> tt_umd.TTDevice:
            if chip_id not in self.devices:
                raise RuntimeError(f"Device with chip id {chip_id} not found.")
            return self.devices[chip_id]

        def get_noc0_to_device_coords(self, chip_id: int, noc_x: int, noc_y: int):
            soc_descriptor = self.soc_descriptors[chip_id]
            noc0_coord = soc_descriptor.get_coord_at(tt_umd.tt_xy_pair(noc_x, noc_y), tt_umd.CoordSystem.NOC0)
            translated_coord = soc_descriptor.translate_coord_to(noc0_coord, tt_umd.CoordSystem.TRANSLATED)
            return tt_umd.tt_xy_pair(translated_coord.x, translated_coord.y)

        def is_chip_mmio_capable(self, chip_id: int) -> bool:
            return self.cluster_descriptor.is_chip_mmio_capable(chip_id)

        def get_arc_telemetry_reader(self, chip_id: int):
            if self.cached_arc_telemetry_readers[chip_id] is None:
                self.cached_arc_telemetry_readers[chip_id] = tt_umd.ArcTelemetryReader.create_arc_telemetry_reader(
                    self.devices[chip_id]
                )
            return self.cached_arc_telemetry_readers[chip_id]

        def read_from_device_reg_unaligned(
            self, device: tt_umd.TTDevice, noc_id: int, noc_coords: tt_umd.tt_xy_pair, address: int, size: int
        ) -> bytes:
            # TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
            tt_umd.TTDevice.use_noc1(noc_id == 1)

            # Read first unaligned word
            first_unaligned_index = address % 4
            if first_unaligned_index != 0:
                temp = device.read_from_device(noc_coords, address - first_unaligned_index, 4)
                if first_unaligned_index + size <= 4:
                    return temp[first_unaligned_index : first_unaligned_index + size]
                mem_ptr = bytearray()
                mem_ptr.extend(temp[first_unaligned_index:4])
                address += 4 - first_unaligned_index
                size -= 4 - first_unaligned_index
            else:
                mem_ptr = bytearray()

            # Read aligned bytes
            aligned_size = size - (size % 4)
            if aligned_size > 0:
                mem_ptr.extend(device.read_from_device(noc_coords, address, aligned_size))
                address += aligned_size
                size -= aligned_size

            # Read last unaligned word
            last_unaligned_size = size
            if last_unaligned_size != 0:
                temp = device.read_from_device(noc_coords, address, 4)
                mem_ptr.extend(temp[:last_unaligned_size])

            return bytes(mem_ptr)

        def write_to_device_reg_unaligned(
            self, device: tt_umd.TTDevice, mem_ptr: bytes, noc_id: int, noc_coords: tt_umd.tt_xy_pair, address: int
        ):
            # TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
            tt_umd.TTDevice.use_noc1(noc_id == 1)

            size_in_bytes = len(mem_ptr)

            # Read/Write first unaligned word
            first_unaligned_index = address % 4
            if first_unaligned_index != 0:
                aligned_address = address - first_unaligned_index
                temp = device.read_from_device(noc_coords, aligned_address, 4)
                if first_unaligned_index + size_in_bytes <= 4:
                    temp = (
                        temp[0:first_unaligned_index]
                        + mem_ptr[0:size_in_bytes]
                        + temp[first_unaligned_index + size_in_bytes : 4]
                    )
                    device.write_to_device(temp, noc_coords, aligned_address)
                    return
                temp = temp[0:first_unaligned_index] + mem_ptr[0 : 4 - first_unaligned_index]
                device.write_to_device(temp, noc_coords, aligned_address)
                mem_ptr = mem_ptr[4 - first_unaligned_index :]
                address += 4 - first_unaligned_index
                size_in_bytes -= 4 - first_unaligned_index

            # Write aligned bytes
            aligned_size = size_in_bytes - (size_in_bytes % 4)
            if aligned_size > 0:
                device.write_to_device(mem_ptr[0:aligned_size], noc_coords, address)
                mem_ptr = mem_ptr[aligned_size:]
                address += aligned_size
                size_in_bytes -= aligned_size

            # Read/Write last unaligned word
            last_unaligned_size = size_in_bytes
            if last_unaligned_size != 0:
                temp = device.read_from_device(noc_coords, address, 4)
                temp = mem_ptr[0:last_unaligned_size] + temp[last_unaligned_size:4]
                device.write_to_device(temp, noc_coords, address)

        def read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int) -> int:
            result = self.read_from_device_reg_unaligned(
                self.get_device(chip_id), noc_id, self.get_noc0_to_device_coords(chip_id, noc_x, noc_y), address, 4
            )
            return int.from_bytes(result, byteorder="little")

        def write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int) -> int:
            self.write_to_device_reg_unaligned(
                self.get_device(chip_id),
                data.to_bytes(4, byteorder="little"),
                noc_id,
                self.get_noc0_to_device_coords(chip_id, noc_x, noc_y),
                address,
            )
            return 4

        def read(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, size: int) -> bytes:
            device = self.get_device(chip_id)
            noc_coords = self.get_noc0_to_device_coords(chip_id, noc_x, noc_y)

            # TODO #124: Mitigation for UMD bug #77
            if not self.is_chip_mmio_capable(chip_id):
                result = bytearray()
                done = 0
                while done < size:
                    block = min(size - done, 1024)
                    result.extend(
                        self.read_from_device_reg_unaligned(device, noc_id, noc_coords, address + done, block)
                    )
                    done += block
                return bytes(result)
            return self.read_from_device_reg_unaligned(device, noc_id, noc_coords, address, size)

        def write(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes) -> int:
            size = len(data)
            device = self.get_device(chip_id)
            noc_coords = self.get_noc0_to_device_coords(chip_id, noc_x, noc_y)

            # TODO #124: Mitigation for UMD bug #77
            if not self.is_chip_mmio_capable(chip_id):
                done = 0
                while done < size:
                    block = min(size - done, 1024)
                    self.write_to_device_reg_unaligned(
                        device, data[done : done + block], noc_id, noc_coords, address + done
                    )
                    done += block
                return size

            self.write_to_device_reg_unaligned(device, data, noc_id, noc_coords, address)
            return size

        def pci_read32_raw(self, chip_id: int, address: int) -> int:
            if self.is_chip_mmio_capable(chip_id):
                return self.get_device(chip_id).bar_read32(address)
            raise RuntimeError(f"Device with chip id {chip_id} is not mmio capable.")

        def pci_write32_raw(self, chip_id: int, address: int, data: int) -> int:
            if self.is_chip_mmio_capable(chip_id):
                return self.get_device(chip_id).bar_write32(address, data)
            raise RuntimeError(f"Device with chip id {chip_id} is not mmio capable.")

        def dma_buffer_read32(self, chip_id: int, address: int, channel: int) -> int:
            raise NotImplementedError("dma_buffer_read32 is not implemented in UMD implementation.")

        def pci_read_tile(
            self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, size: int, data_format: int
        ) -> bytes:
            raise NotImplementedError("pci_read_tile is not implemented in UMD implementation.")

        def get_cluster_description(self):
            return self.cluster_descriptor_path

        def get_device_ids(self):
            return self.device_ids

        def get_device_arch(self, chip_id: int) -> str:
            return str(self.devices[chip_id].get_arch())

        def get_device_soc_description(self, chip_id: int) -> str:
            return self.device_soc_descriptors_yamls[chip_id]

        def convert_from_noc0(self, chip_id: int, noc_x: int, noc_y: int, core_type: str, coord_system: str):
            if core_type == "arc":
                core_type_enum = tt_umd.CoreType.ARC
            elif core_type == "dram":
                core_type_enum = tt_umd.CoreType.DRAM
            elif core_type == "active_eth":
                core_type_enum = tt_umd.CoreType.ACTIVE_ETH
            elif core_type == "idle_eth":
                core_type_enum = tt_umd.CoreType.IDLE_ETH
            elif core_type == "pcie":
                core_type_enum = tt_umd.CoreType.PCIE
            elif core_type == "tensix":
                core_type_enum = tt_umd.CoreType.TENSIX
            elif core_type == "router_only":
                core_type_enum = tt_umd.CoreType.ROUTER_ONLY
            elif core_type == "harvested":
                core_type_enum = tt_umd.CoreType.HARVESTED
            elif core_type == "eth":
                core_type_enum = tt_umd.CoreType.ETH
            elif core_type == "worker":
                core_type_enum = tt_umd.CoreType.WORKER
            elif core_type == "security":
                core_type_enum = tt_umd.CoreType.SECURITY
            elif core_type == "l2cpu":
                core_type_enum = tt_umd.CoreType.L2CPU
            else:
                raise RuntimeError(f"Unknown core type: {core_type}")

            if coord_system == "logical":
                coord_system_enum = tt_umd.CoordSystem.LOGICAL
            elif coord_system == "translated":
                coord_system_enum = tt_umd.CoordSystem.TRANSLATED
            elif coord_system == "noc0":
                coord_system_enum = tt_umd.CoordSystem.NOC0
            elif coord_system == "noc1":
                coord_system_enum = tt_umd.CoordSystem.NOC1
            else:
                raise RuntimeError(f"Unknown coordinate system: {coord_system}")

            soc_descriptor = self.soc_descriptors[chip_id]
            core_coord = tt_umd.CoreCoord(noc_x, noc_y, core_type_enum, tt_umd.CoordSystem.NOC0)
            output = soc_descriptor.translate_coord_to(core_coord, coord_system_enum)
            return (output.x, output.y)

        def arc_msg(
            self, noc_id: int, chip_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int
        ):
            # TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
            tt_umd.TTDevice.use_noc1(noc_id == 1)

            return self.get_device(chip_id).get_arc_messenger().send_message(msg_code, arg0, arg1, timeout)

        def read_arc_telemetry_entry(self, chip_id: int, telemetry_tag: int) -> int | None:
            arc_telemetry_reader = self.get_arc_telemetry_reader(chip_id)
            umd_telemetry_tag = tt_umd.TelemetryTag(telemetry_tag)
            if not arc_telemetry_reader.is_entry_available(umd_telemetry_tag):
                return None
            return arc_telemetry_reader.read_entry(umd_telemetry_tag)

        def get_firmware_version(self, chip_id: int):
            tt_device = self.get_device(chip_id)
            firmware_version = tt_device.get_firmware_version()
            return (firmware_version.major, firmware_version.minor, firmware_version.patch)

        def get_device_unique_id(self, chip_id: int) -> int:
            return self.device_id_to_unique_id[chip_id]

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
    TTExaLensUmdImplementation = TTExaLensPybind


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
