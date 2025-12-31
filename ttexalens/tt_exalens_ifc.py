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
    from contextlib import contextmanager
    import datetime
    import tempfile
    import time
    from typing import Sequence
    import tt_umd
    import threading

    umd_noc_lock = threading.Lock()

    @contextmanager
    def switch_umd_noc(noc_id: int):
        with umd_noc_lock:
            tt_umd.TTDevice.use_noc1(noc_id == 1)
            yield

    class TimeoutDeviceRegisterError(Exception):
        def __init__(
            self, chip_id: int, coord: tt_umd.CoreCoord, address: int, size: int, is_read: bool, duration_us: float
        ):
            self.chip_id = chip_id
            self.coord = coord
            self.address = address
            self.size = size
            self.is_read = is_read
            self.duration_us = duration_us

        def __str__(self):
            operation = "read" if self.is_read else "write"
            return (
                f"TimeoutDeviceRegisterError: Timeout during {operation} operation on device {self.chip_id}, "
                f"coord ({self.coord.x}, {self.coord.y}, {self.coord.core_type}), address {hex(self.address)}, "
                f"size {self.size} bytes after {self.duration_us:.2f} us."
            )

    class UmdDeviceWrapper:
        def __init__(
            self,
            device: tt_umd.TTDevice,
            device_id: int,
            unique_id: int,
            active_eth_coords_on_mmio_chip: list[tuple[int, int]] = [],
            soc_descriptor: tt_umd.SocDescriptor | None = None,
            is_simulation: bool = False,
        ):
            self.__device = device
            self.arch = device.get_arch()
            self.is_mmio_capable = not device.is_remote()
            self.soc_descriptor = soc_descriptor if soc_descriptor is not None else tt_umd.SocDescriptor(device)
            self.device_id = device_id
            self.unique_id = unique_id
            self.active_eth_coords_on_mmio_chip = active_eth_coords_on_mmio_chip  # in translated coords
            self.is_simulation = is_simulation

            # TODO: Until UMD implements timeout exception, we measure time here
            self.__write_timeout_lock = threading.Lock()
            self.__write_timeout_events: list[TimeoutDeviceRegisterError] = []

        def __configure_working_active_eth(self):
            tensix_coord = tt_umd.CoreCoord(0, 0, tt_umd.CoreType.TENSIX, tt_umd.CoordSystem.LOGICAL)
            tensix_translated_coord = self.soc_descriptor.translate_coord_to(
                tensix_coord, tt_umd.CoordSystem.TRANSLATED
            )
            for translated_coord in self.active_eth_coords_on_mmio_chip:
                self.__device.get_remote_communication().set_remote_transfer_ethernet_cores([translated_coord])
                try:
                    self.__read_from_device_reg(tensix_translated_coord.x, tensix_translated_coord.y, 0, 4)
                    return
                except:
                    continue
            raise RuntimeError("Failed to configure working active Ethernet")  # TODO: Improve error message

        def __convert_noc0_to_device_coords(self, noc0_x: int, noc0_y: int):
            return self.soc_descriptor.translate_coord_to(
                tt_umd.tt_xy_pair(noc0_x, noc0_y), tt_umd.CoordSystem.NOC0, tt_umd.CoordSystem.TRANSLATED
            )

        READ_TIMEOUT = float(os.environ.get("TT_EXALENS_READ_TIMEOUT_MS", 2)) / 1_000  # seconds
        WRITE_TIMEOUT = float(os.environ.get("TT_EXALENS_WRITE_TIMEOUT_MS", 2)) / 1_000  # seconds
        NUM_OF_CONSECUTIVE_TIMEOUTS = int(os.environ.get("TT_EXALENS_NUM_OF_CONSECUTIVE_TIMEOUTS", 5))

        def __read_from_device_reg(self, coord_x: int, coord_y: int, address: int, size: int) -> bytes:
            # TODO: Until UMD implements timeout exception, we measure time here
            start_time = time.time()
            result = self.__device.noc_read(coord_x, coord_y, address, size)
            end_time = time.time()
            elapsed_time = end_time - start_time  # seconds
            if (
                self.is_mmio_capable
                and not self.is_simulation
                and elapsed_time > UmdDeviceWrapper.READ_TIMEOUT
                and result[-4:] == b"\xFF\xFF\xFF\xFF"
            ):
                translated_coord = self.soc_descriptor.translate_coord_to(
                    tt_umd.tt_xy_pair(coord_x, coord_y), tt_umd.CoordSystem.TRANSLATED, tt_umd.CoordSystem.LOGICAL
                )
                raise TimeoutDeviceRegisterError(self.device_id, translated_coord, address, size, True, elapsed_time)
            return result

        def __write_to_device_reg(self, coord_x: int, coord_y: int, address: int, data: bytes):
            # TODO: Until UMD implements timeout exception, we measure time here
            start_time = time.time()
            self.__device.noc_write(coord_x, coord_y, address, data)
            end_time = time.time()
            elapsed_time = end_time - start_time  # seconds
            if (
                self.is_mmio_capable
                and not self.is_simulation
                and len(data) == 4
                and elapsed_time > UmdDeviceWrapper.WRITE_TIMEOUT
            ):
                translated_coord = self.soc_descriptor.translate_coord_to(
                    tt_umd.tt_xy_pair(coord_x, coord_y), tt_umd.CoordSystem.TRANSLATED, tt_umd.CoordSystem.LOGICAL
                )
                event = TimeoutDeviceRegisterError(
                    self.device_id, translated_coord, address, len(data), False, elapsed_time
                )
                with self.__write_timeout_lock:
                    self.__write_timeout_events.append(event)
                    if len(self.__write_timeout_events) >= UmdDeviceWrapper.NUM_OF_CONSECUTIVE_TIMEOUTS:
                        raise self.__write_timeout_events[0]
            else:
                with self.__write_timeout_lock:
                    self.__write_timeout_events.clear()

        def __read_from_device_reg_unaligned_helper(
            self, coord: tt_umd.CoreCoord, address: int, size: int, use_4B_mode: bool
        ) -> bytes:
            assert coord.coord_system == tt_umd.CoordSystem.TRANSLATED

            # Read first unaligned word
            first_unaligned_index = address % 4
            if first_unaligned_index != 0:
                temp = self.__read_from_device_reg(coord.x, coord.y, address - first_unaligned_index, 4)
                if first_unaligned_index + size <= 4:
                    return temp[first_unaligned_index : first_unaligned_index + size]
                data = bytearray()
                data.extend(temp[first_unaligned_index:4])
                address += 4 - first_unaligned_index
                size -= 4 - first_unaligned_index
            else:
                data = bytearray()

            # Read aligned bytes
            aligned_size = size - (size % 4)
            block_size = 4 if use_4B_mode and not self.is_simulation else aligned_size
            while aligned_size > 0:
                data.extend(self.__read_from_device_reg(coord.x, coord.y, address, block_size))
                aligned_size -= block_size
                address += block_size
                size -= block_size

            # Read last unaligned word
            last_unaligned_size = size
            if last_unaligned_size != 0:
                temp = self.__read_from_device_reg(coord.x, coord.y, address, 4)
                data.extend(temp[:last_unaligned_size])

            return bytes(data)

        def __read_from_device_reg_unaligned(
            self, noc_id: int, noc0_x: int, noc0_y: int, address: int, size: int, use_4B_mode: bool
        ) -> bytes:
            # TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
            with switch_umd_noc(noc_id):
                coord = self.__convert_noc0_to_device_coords(noc0_x, noc0_y)
                try:
                    return self.__read_from_device_reg_unaligned_helper(coord, address, size, use_4B_mode)
                except TimeoutDeviceRegisterError as e:
                    raise
                except:
                    if self.is_simulation or self.is_mmio_capable:
                        raise
                    self.__configure_working_active_eth()
                    return self.__read_from_device_reg_unaligned_helper(coord, address, size, use_4B_mode)

        def __write_to_device_reg_unaligned_helper(
            self, coord: tt_umd.CoreCoord, address: int, data: bytes, use_4B_mode: bool
        ):
            assert coord.coord_system == tt_umd.CoordSystem.TRANSLATED
            size_in_bytes = len(data)

            # Read/Write first unaligned word
            first_unaligned_index = address % 4
            if first_unaligned_index != 0:
                aligned_address = address - first_unaligned_index
                temp = self.__read_from_device_reg(coord.x, coord.y, aligned_address, 4)
                if first_unaligned_index + size_in_bytes <= 4:
                    temp = (
                        temp[0:first_unaligned_index]
                        + data[0:size_in_bytes]
                        + temp[first_unaligned_index + size_in_bytes : 4]
                    )
                    self.__write_to_device_reg(coord.x, coord.y, aligned_address, temp)
                    return
                temp = temp[0:first_unaligned_index] + data[0 : 4 - first_unaligned_index]
                self.__write_to_device_reg(coord.x, coord.y, aligned_address, temp)
                data = data[4 - first_unaligned_index :]
                address += 4 - first_unaligned_index
                size_in_bytes -= 4 - first_unaligned_index

            # Write aligned bytes
            aligned_size = size_in_bytes - (size_in_bytes % 4)
            block_size = 4 if use_4B_mode and not self.is_simulation else aligned_size
            offset = 0
            while aligned_size > 0:
                self.__write_to_device_reg(coord.x, coord.y, address, data[offset : offset + block_size])
                aligned_size -= block_size
                offset += block_size
                address += block_size
                size_in_bytes -= block_size
            data = data[offset:]

            # Read/Write last unaligned word
            last_unaligned_size = size_in_bytes
            if last_unaligned_size != 0:
                temp = self.__read_from_device_reg(coord.x, coord.y, address, 4)
                temp = data[0:last_unaligned_size] + temp[last_unaligned_size:4]
                self.__write_to_device_reg(coord.x, coord.y, address, temp)

        def __write_to_device_reg_unaligned(
            self, noc_id: int, noc0_x: int, noc0_y: int, address: int, data: bytes, use_4B_mode: bool
        ):
            # TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
            with switch_umd_noc(noc_id):
                coord = self.__convert_noc0_to_device_coords(noc0_x, noc0_y)
                try:
                    self.__write_to_device_reg_unaligned_helper(coord, address, data, use_4B_mode)
                except TimeoutDeviceRegisterError as e:
                    raise
                except:
                    if self.is_simulation or self.is_mmio_capable:
                        raise
                    self.__configure_working_active_eth()
                    self.__write_to_device_reg_unaligned_helper(coord, address, data, use_4B_mode)

        ##################################################################
        ## OLD API METHODS FROM TTExaLensImplementation TO BE FORWARDED ##
        ##################################################################

        def read32(self, noc_id: int, noc0_x: int, noc0_y: int, address: int) -> int:
            """Reads 4 bytes from address"""
            result = self.__read_from_device_reg_unaligned(noc_id, noc0_x, noc0_y, address, 4, True)
            return int.from_bytes(result, byteorder="little")

        def write32(self, noc_id: int, noc0_x: int, noc0_y: int, address: int, data: int) -> int:
            """Writes 4 bytes to address"""
            self.__write_to_device_reg_unaligned(
                noc_id, noc0_x, noc0_y, address, data.to_bytes(4, byteorder="little"), True
            )
            return 4

        def read(self, noc_id: int, noc0_x: int, noc0_y: int, address: int, size: int, use_4B_mode: bool) -> bytes:
            """Reads data from address"""
            # TODO #124: Mitigation for UMD bug #77
            if not self.is_mmio_capable:
                result = bytearray()
                for chunk_start in range(0, size, 1024):
                    chunk_size = min(1024, size - chunk_start)
                    result.extend(
                        self.__read_from_device_reg_unaligned(
                            noc_id, noc0_x, noc0_y, address + chunk_start, chunk_size, use_4B_mode
                        )
                    )
                return bytes(result)
            return self.__read_from_device_reg_unaligned(noc_id, noc0_x, noc0_y, address, size, use_4B_mode)

        def write(self, noc_id: int, noc0_x: int, noc0_y: int, address: int, data: bytes, use_4B_mode: bool) -> int:
            """Writes data to address"""
            size = len(data)
            # TODO #124: Mitigation for UMD bug #77
            if not self.is_mmio_capable:
                for chunk_start in range(0, size, 1024):
                    chunk_size = min(1024, size - chunk_start)
                    self.__write_to_device_reg_unaligned(
                        noc_id,
                        noc0_x,
                        noc0_y,
                        address + chunk_start,
                        data[chunk_start : chunk_start + chunk_size],
                        use_4B_mode,
                    )
                return size
            self.__write_to_device_reg_unaligned(noc_id, noc0_x, noc0_y, address, data, use_4B_mode)
            return size

        def pci_read32_raw(self, address: int) -> int:
            """Reads 4 bytes from PCI address"""
            if self.is_mmio_capable:
                return self.__device.bar_read32(address)
            raise RuntimeError("Device is not mmio capable.")

        def pci_write32_raw(self, address: int, data: int) -> int:
            """Writes 4 bytes to PCI address"""
            if self.is_mmio_capable:
                self.__device.bar_write32(address, data)
                return 4
            raise RuntimeError("Device is not mmio capable.")

        def dma_buffer_read32(self, address: int, channel: int) -> int:
            """Reads 4 bytes from DMA buffer"""
            raise NotImplementedError("dma_buffer_read32 is not implemented in UmdDeviceWrapper.")

        def pci_read_tile(self, noc_id: int, noc_x: int, noc_y: int, address: int, size: int, data_format: int) -> str:
            """Reads tile from address"""
            raise NotImplementedError("pci_read_tile is not implemented in UmdDeviceWrapper.")

        def convert_from_noc0(self, noc_x: int, noc_y: int, core_type: str, coord_system: str) -> tuple[int, int]:
            """Convert noc0 coordinate into specified coordinate system"""
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

            core_coord = tt_umd.CoreCoord(noc_x, noc_y, core_type_enum, tt_umd.CoordSystem.NOC0)
            output = self.soc_descriptor.translate_coord_to(core_coord, coord_system_enum)
            return (output.x, output.y)

        def arc_msg(
            self,
            noc_id: int,
            msg_code: int,
            wait_for_done: bool,
            args: Sequence[int],
            timeout: datetime.timedelta | float,
        ) -> tuple[int, int, int]:
            """Send ARC message"""
            # TODO: Hack on UMD on how to use noc1. This should be removed once we have a proper way to use noc1.
            with switch_umd_noc(noc_id):
                timeout_ms = (
                    timeout.total_seconds() * 1000 if isinstance(timeout, datetime.timedelta) else timeout * 1000
                )
                return self.__device.arc_msg(msg_code, wait_for_done, args, int(timeout_ms))

        def read_arc_telemetry_entry(self, telemetry_tag: int) -> int:
            """Read ARC telemetry entry"""

            def do_read(telemetry_tag: int) -> int:
                arc_telemetry_reader = self.__device.get_arc_telemetry_reader()
                if not arc_telemetry_reader.is_entry_available(telemetry_tag):
                    raise RuntimeError(f"Telemetry tag {telemetry_tag} is not available on device {self.device_id}.")
                return arc_telemetry_reader.read_entry(telemetry_tag)

            try:
                return do_read(telemetry_tag)
            except:
                if not self.is_mmio_capable:
                    raise
                # TODO: We should retry only if it was remote read error
                self.__configure_working_active_eth()
                return do_read(telemetry_tag)

        def get_firmware_version(self) -> tuple[int, int, int]:
            """Returns firmware version"""

            def do_read():
                firmware_info_provider = self.__device.get_firmware_info_provider()
                return firmware_info_provider.get_firmware_version()

            try:
                firmware_version = do_read()
            except:
                if not self.is_mmio_capable:
                    raise
                # TODO: We should retry only if it was remote read error
                self.__configure_working_active_eth()
                firmware_version = do_read()
            return (firmware_version.major, firmware_version.minor, firmware_version.patch)

        def get_remote_transfer_eth_core(self) -> tuple[int, int] | None:
            """Returns currently active Ethernet core in logical coordinates"""
            remote_communication = self.__device.get_remote_communication()
            if remote_communication is None:
                return None
            translated_coord = remote_communication.get_remote_transfer_ethernet_core()
            local_device = remote_communication.get_local_device()
            logical_coord = tt_umd.SocDescriptor(local_device).translate_coord_to(
                tt_umd.CoreCoord(
                    translated_coord[0], translated_coord[1], tt_umd.CoreType.ETH, tt_umd.CoordSystem.TRANSLATED
                ),
                tt_umd.CoordSystem.LOGICAL,
            )
            return (logical_coord.x, logical_coord.y)

    class TTExaLensUmdImplementation(TTExaLensCommunicator):
        def __init__(
            self,
            wanted_devices: list = [],
            init_jtag=False,
            initialize_with_noc1=False,
            simulation_directory: str | None = None,
        ):
            self.temp_working_directory = tempfile.mkdtemp(prefix="ttexalens_server_XXXXXX")
            self.cluster_descriptor_path = os.path.join(self.temp_working_directory, "cluster_desc.yaml")
            self.device_soc_descriptors_yamls: dict[int, str] = {}
            self.devices: dict[int, UmdDeviceWrapper] = {}
            self.device_ids: list[int] = []

            # Respect UMD's existing env var first; default to ERROR otherwise.
            # If Python wants DEBUG, it can set TT_LOGGER_LEVEL=debug before calling into this function.
            if "TT_LOGGER_LEVEL" not in os.environ:
                tt_umd.logging.set_level(
                    tt_umd.logging.Level.Error if simulation_directory is None else tt_umd.logging.Level.Debug
                )

            # TODO: Hack on UMD on how to use/initialize with noc1. This should be removed once we have a proper way to use noc1
            tt_umd.TTDevice.use_noc1(initialize_with_noc1)

            if simulation_directory is not None:
                tt_device = tt_umd.RtlSimulationTTDevice.create(simulation_directory)
                soc_descriptor = tt_device.get_soc_descriptor()
                if tt_device.get_arch() == tt_umd.ARCH.BLACKHOLE:
                    # Fix for old VSC Blackhole simulator
                    for core in soc_descriptor.get_cores(tt_umd.CoreType.TENSIX):
                        core_noc0 = soc_descriptor.translate_coord_to(core, tt_umd.CoordSystem.NOC0)
                        tt_device.noc_write32(core_noc0.x, core_noc0.y, 0, 0x6F)
                        tt_device.send_tensix_risc_reset(tt_umd.tt_xy_pair(core.x, core.y), deassert=True)
                self.devices[0] = UmdDeviceWrapper(tt_device, 0, 0, soc_descriptor=soc_descriptor, is_simulation=True)
                self.device_ids.append(0)
                with open(self.cluster_descriptor_path, "w") as f:
                    f.write(f"arch: {{\n")
                    f.write(f"   0: {self.devices[0].arch},\n")
                    f.write(f"}}\n\n")
                    f.write(f"chips: {{\n")
                    f.write(f"   0: [0,0,0,0],\n")
                    f.write(f"}}\n\n")
                    f.write(f"ethernet_connections: [\n")
                    f.write(f"]\n\n")
                    f.write(f"chips_with_mmio: [\n")
                    f.write(f"   0: 0,\n")
                    f.write(f"]\n\n")
                    f.write(
                        f"# harvest_mask is the bit indicating which tensix row is harvested. So bit 0 = first tensix row; bit 1 = second tensix row etc...\n"
                    )
                    f.write(f"harvesting: {{\n")
                    f.write(f"   0: {{noc_translation: false, harvest_mask: 0}},\n")
                    f.write(f"}}\n\n")
                    f.write(
                        f"# This value will be null if the boardtype is unknown, should never happen in practice but to be defensive it would be useful to throw an error on this case.\n"
                    )
                    f.write(f"boardtype: {{\n")
                    f.write(f"   0: {self.devices[0].arch}Simulator,\n")
                    f.write(f"}}\n")
                    f.write(f"io_device_type: SIMULATION\n")
                # TODO: In destructor we need to call close device so that emulation can stop reservation and simulation can stop waveform?!?
            else:
                discovery_options = tt_umd.TopologyDiscoveryOptions()
                discovery_options.io_device_type = (
                    tt_umd.IODeviceType.PCIe if not init_jtag else tt_umd.IODeviceType.JTAG
                )
                # TODO: discovery_options.no_wait_for_eth_training = True
                # TODO: discovery_options.no_eth_firmware_strictness = True
                self.cluster_descriptor, devices = tt_umd.TopologyDiscovery.discover(discovery_options)

                if len(self.cluster_descriptor.get_all_chips()) == 0:
                    raise RuntimeError("No Tenstorrent devices were detected on this system.")
                self.cluster_descriptor.serialize_to_file(self.cluster_descriptor_path)

                # Setup used devices
                for i in self.cluster_descriptor.get_all_chips():
                    self.device_ids.append(i)

                device_id_to_unique_id = {}
                unique_ids = self.cluster_descriptor.get_chip_unique_ids()
                for device_id in self.device_ids:
                    if device_id in unique_ids:
                        device_id_to_unique_id[device_id] = unique_ids[device_id]

                # If we specified which devices we want, check that they are available and then extract their ids
                if len(wanted_devices) > 0:
                    for wanted_device in wanted_devices:
                        if wanted_device not in self.device_ids:
                            raise RuntimeError(f"Device {wanted_device} is not available.")
                    self.device_ids = wanted_devices

                for chip_id in self.device_ids:
                    device = devices[chip_id]
                    unique_id = device_id_to_unique_id.get(chip_id, None)
                    assert unique_id is not None, f"Unique ID for device {chip_id} not found."

                    if not self.cluster_descriptor.is_chip_mmio_capable(chip_id):
                        soc_descriptor = tt_umd.SocDescriptor(device)
                        mmio_chip_id = self.cluster_descriptor.get_closest_mmio_capable_chip(chip_id)
                        active_eth_channels = self.cluster_descriptor.get_active_eth_channels(mmio_chip_id)
                        active_eth_cores = soc_descriptor.get_eth_cores_for_channels(
                            active_eth_channels, tt_umd.CoordSystem.TRANSLATED
                        )
                        active_eth_coords_on_mmio_chip = [(core.x, core.y) for core in active_eth_cores]
                    else:
                        active_eth_coords_on_mmio_chip = []

                    wrapped_device = UmdDeviceWrapper(device, chip_id, unique_id, active_eth_coords_on_mmio_chip)
                    assert wrapped_device.is_mmio_capable == self.cluster_descriptor.is_chip_mmio_capable(chip_id)
                    self.devices[chip_id] = wrapped_device

            for chip_id, wrapped_device in self.devices.items():
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
