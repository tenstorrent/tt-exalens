# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from contextlib import contextmanager
import datetime
import os
import threading
import time
from typing import Sequence
import tt_umd

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
        tensix_translated_coord = self.soc_descriptor.translate_coord_to(tensix_coord, tt_umd.CoordSystem.TRANSLATED)
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
            timeout_ms = timeout.total_seconds() * 1000 if isinstance(timeout, datetime.timedelta) else timeout * 1000
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
