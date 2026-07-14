# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import datetime
import traceback
from typing import Sequence
import tt_umd
from ttexalens import util
from ttexalens.exceptions import TimeoutDeviceRegisterError
from ttexalens.umd_api import UmdApi


class UmdDevice:
    def __init__(
        self,
        api: UmdApi,
        device: tt_umd.TTDevice,
        device_id: int,
        unique_id: int,
        active_eth_coords_on_mmio_chip: list[tuple[int, int]] = [],
        soc_descriptor: tt_umd.SocDescriptor | None = None,
        cluster_descriptor: tt_umd.ClusterDescriptor | None = None,
        is_simulation: bool = False,
    ):
        # IMPORTANT:
        # This class is a wrapper around tt_umd.TTDevice that allows us to use it over tt-exalens server.
        # It cannot have public members (value attributes) because they won't be serialized by Pyro5.
        # Instead, all public members must be properties with getter/setter methods.
        self.__api = api
        self.__device = device
        self._arch = device.get_arch()
        self._is_mmio_capable = not device.is_remote()
        self._is_jtag_capable = device.get_communication_device_type() == tt_umd.IODeviceType.JTAG
        self._soc_descriptor = soc_descriptor if soc_descriptor is not None else tt_umd.SocDescriptor(device)
        self._device_id = device_id
        self._unique_id = unique_id
        self._active_eth_coords_on_mmio_chip = active_eth_coords_on_mmio_chip  # in translated coords
        self._is_simulation = is_simulation
        self.__device_coords = UmdDevice.initialize_device_coords_cache(self._soc_descriptor, self._arch)

        # On T3K we observed slower communication over default active ETH, so we try to switch to another active ETH if available.
        if (
            device.is_remote()
            and cluster_descriptor is not None
            and cluster_descriptor.get_board_type(device_id) == tt_umd.BoardType.N300
        ):
            if len(active_eth_coords_on_mmio_chip) > 1:
                self._active_eth_coords_on_mmio_chip = (
                    active_eth_coords_on_mmio_chip[1:] + active_eth_coords_on_mmio_chip[:1]
                )
            self.__configure_working_active_eth()

    @staticmethod
    def initialize_device_coords_cache(
        soc_descriptor: tt_umd.SocDescriptor, arch: tt_umd.ARCH
    ) -> list[list[list[tt_umd.CoreCoord | None]] | None]:
        all_cores = soc_descriptor.get_all_cores(
            coord_system=tt_umd.CoordSystem.NOC0
        ) + soc_descriptor.get_all_harvested_cores(coord_system=tt_umd.CoordSystem.NOC0)

        max_x = max(core.x for core in all_cores) + 1
        max_y = max(core.y for core in all_cores) + 1
        supported_noc_ids = (
            [tt_umd.NocId.NOC0, tt_umd.NocId.SYSTEM_NOC]
            if arch == tt_umd.ARCH.QUASAR
            else [tt_umd.NocId.NOC0, tt_umd.NocId.NOC1]
        )
        result: list[list[list[tt_umd.CoreCoord | None]] | None] = [None] * (max(int(n) for n in supported_noc_ids) + 1)
        for noc_id in supported_noc_ids:
            UmdApi.select_noc_id(noc_id, arch)
            noc_result: list[list[tt_umd.CoreCoord | None]] = []
            for x in range(max_x):
                row: list[tt_umd.CoreCoord | None] = []
                for y in range(max_y):
                    try:
                        coords = soc_descriptor.translate_chip_coord_to_translated_coord(
                            soc_descriptor.get_coord_at(tt_umd.tt_xy_pair(x, y), tt_umd.CoordSystem.NOC0)
                        )
                        row.append(coords)
                    except Exception:
                        row.append(None)
                noc_result.append(row)
            result[int(noc_id)] = noc_result
        return result

    @property
    def device_id(self) -> int:
        return self._device_id

    @property
    def unique_id(self) -> int:
        return self._unique_id

    @property
    def arch(self) -> tt_umd.ARCH:
        return self._arch

    @property
    def soc_descriptor(self) -> tt_umd.SocDescriptor:
        return self._soc_descriptor

    @property
    def is_mmio_capable(self) -> bool:
        return self._is_mmio_capable

    @property
    def is_jtag_capable(self) -> bool:
        return self._is_jtag_capable

    @property
    def is_simulation(self) -> bool:
        return self._is_simulation

    @property
    def can_use_dma(self) -> bool:
        return self._arch != tt_umd.ARCH.BLACKHOLE and self._is_mmio_capable and not self._is_simulation

    def __select_noc_id(self, noc_id: tt_umd.NocId):
        UmdApi.select_noc_id(noc_id, self._arch)

    def __configure_working_active_eth(self):
        tensix_coord = tt_umd.CoreCoord(0, 0, tt_umd.CoreType.TENSIX, tt_umd.CoordSystem.LOGICAL)
        tensix_translated_coord = self._soc_descriptor.translate_chip_coord_to_translated_coord(tensix_coord)
        buffer = bytearray(4)
        for translated_coord in self._active_eth_coords_on_mmio_chip:
            self.__device.get_remote_communication().set_remote_transfer_ethernet_cores([translated_coord])
            try:
                self.__read_from_device_reg(tensix_translated_coord, 0, buffer, 8)
                return
            except Exception:
                if util.DEBUG_ENABLED:
                    util.DEBUG(
                        f"Active ETH core {translated_coord} not working, trying next:\n{traceback.format_exc()}"
                    )
                continue
        raise RuntimeError("Failed to configure working active Ethernet")  # TODO: Improve error message

    def __convert_noc0_to_device_coords(self, noc_id: tt_umd.NocId, noc0_x: int, noc0_y: int):
        return self.__device_coords[int(noc_id)][noc0_x][noc0_y]

    def __read_from_device_reg(
        self, coord: tt_umd.CoreCoord, address: int, buffer: bytearray | memoryview, dma_threshold: int
    ) -> None:
        # Check if we can use DMA read
        if len(buffer) >= dma_threshold and self.can_use_dma:
            self.__device.dma_read_from_device(0, coord.x, coord.y, address, buffer)
        else:
            try:
                self.__device.noc_read(0, coord.x, coord.y, address, buffer)
            except tt_umd.error.DeviceTimeoutError as error:
                # Translate the coordinates to a more user-friendly representation for the error message
                try:
                    translated_coord = self._soc_descriptor.translate_coord_to(coord, tt_umd.CoordSystem.LOGICAL)
                except Exception:
                    try:
                        translated_coord = self._soc_descriptor.translate_coord_to(coord, tt_umd.CoordSystem.NOC0)
                    except Exception:
                        translated_coord = coord

                # Translate the UMD error into a TimeoutDeviceRegisterError and raise it
                raise TimeoutDeviceRegisterError(self.device_id, translated_coord, address, len(buffer), True, error)

    def __write_to_device_reg(
        self, coord: tt_umd.CoreCoord, address: int, data: bytes | bytearray | memoryview, dma_threshold: int
    ):
        # Check if we can use DMA write
        if len(data) >= dma_threshold and self.can_use_dma:
            self.__device.dma_write_to_device(coord.x, coord.y, address, data)
        else:
            try:
                self.__device.noc_write(coord.x, coord.y, address, data)
            except tt_umd.error.DeviceTimeoutError as error:
                # Translate the coordinates to a more user-friendly representation for the error message
                try:
                    translated_coord = self._soc_descriptor.translate_coord_to(coord, tt_umd.CoordSystem.LOGICAL)
                except Exception:
                    try:
                        translated_coord = self._soc_descriptor.translate_coord_to(coord, tt_umd.CoordSystem.NOC0)
                    except Exception:
                        translated_coord = coord
                raise TimeoutDeviceRegisterError(self.device_id, translated_coord, address, len(data), False, error)

    def __read_from_device_reg_unaligned_helper(
        self,
        coord: tt_umd.CoreCoord,
        address: int,
        buffer: bytearray | memoryview,
        dma_threshold: int,
    ) -> None:
        # Read first unaligned word
        first_unaligned_index = address % 4
        size = len(buffer)
        offset = 0
        if first_unaligned_index != 0:
            temp = bytearray(4)
            self.__read_from_device_reg(coord, address - first_unaligned_index, temp, dma_threshold)
            if first_unaligned_index + size <= 4:
                buffer[:size] = temp[first_unaligned_index : first_unaligned_index + size]
                return
            buffer[: 4 - first_unaligned_index] = temp[first_unaligned_index:4]
            offset += 4 - first_unaligned_index
            address += offset
            size -= offset

        # Read aligned bytes. Wrap in a memoryview so that slicing yields a view into the
        # original buffer instead of a temporary copy (slicing a bytearray copies).
        view = memoryview(buffer)
        aligned_size = size - (size % 4)
        if aligned_size > 0:
            self.__read_from_device_reg(coord, address, view[offset : offset + aligned_size], dma_threshold)
            offset += aligned_size
            address += aligned_size
            size -= aligned_size

        # Read last unaligned word
        last_unaligned_size = size
        if last_unaligned_size != 0:
            temp = bytearray(4)
            self.__read_from_device_reg(coord, address, temp, dma_threshold)
            buffer[offset : offset + last_unaligned_size] = temp[:last_unaligned_size]

    def __read_from_device_reg_unaligned(
        self,
        noc_id: tt_umd.NocId,
        noc0_x: int,
        noc0_y: int,
        address: int,
        buffer: bytearray | memoryview,
        dma_threshold: int,
    ) -> None:
        coord = self.__convert_noc0_to_device_coords(noc_id, noc0_x, noc0_y)
        assert coord is not None, f"Invalid NoC0 coordinates: ({noc0_x}, {noc0_y})"
        try:
            self.__read_from_device_reg_unaligned_helper(coord, address, buffer, dma_threshold)
        except TimeoutDeviceRegisterError:
            raise
        except Exception:
            if self._is_simulation or self._is_mmio_capable:
                raise
            if util.DEBUG_ENABLED:
                util.DEBUG(f"Read failed, retrying via ETH reconfiguration:\n{traceback.format_exc()}")
            self.__configure_working_active_eth()
            self.__read_from_device_reg_unaligned_helper(coord, address, buffer, dma_threshold)

    def __write_to_device_reg_unaligned_helper(
        self,
        coord: tt_umd.CoreCoord,
        address: int,
        data: bytes | bytearray | memoryview,
        dma_threshold: int,
    ):
        size_in_bytes = len(data)

        # Read/Write first unaligned word
        first_unaligned_index = address % 4
        if first_unaligned_index != 0:
            aligned_address = address - first_unaligned_index
            temp = bytearray(4)
            self.__read_from_device_reg(coord, aligned_address, temp, dma_threshold)
            if first_unaligned_index + size_in_bytes <= 4:
                temp = (
                    temp[0:first_unaligned_index]
                    + data[0:size_in_bytes]
                    + temp[first_unaligned_index + size_in_bytes : 4]
                )
                self.__write_to_device_reg(coord, aligned_address, temp, dma_threshold)
                return
            temp = temp[0:first_unaligned_index] + data[0 : 4 - first_unaligned_index]
            self.__write_to_device_reg(coord, aligned_address, temp, dma_threshold)
            data = data[4 - first_unaligned_index :]
            address += 4 - first_unaligned_index
            size_in_bytes -= 4 - first_unaligned_index

        # Write aligned bytes
        aligned_size = size_in_bytes - (size_in_bytes % 4)
        offset = 0
        if aligned_size > 0:
            self.__write_to_device_reg(coord, address, data[offset : offset + aligned_size], dma_threshold)
            offset += aligned_size
            address += aligned_size
            size_in_bytes -= aligned_size
        data = data[offset:]

        # Read/Write last unaligned word
        last_unaligned_size = size_in_bytes
        if last_unaligned_size != 0:
            temp = bytearray(4)
            self.__read_from_device_reg(coord, address, temp, dma_threshold)
            temp[0:last_unaligned_size] = data[0:last_unaligned_size]
            self.__write_to_device_reg(coord, address, temp, dma_threshold)

    def __write_to_device_reg_unaligned(
        self,
        noc_id: tt_umd.NocId,
        noc0_x: int,
        noc0_y: int,
        address: int,
        data: bytes | bytearray | memoryview,
        dma_threshold: int,
    ):
        coord = self.__convert_noc0_to_device_coords(noc_id, noc0_x, noc0_y)
        assert coord is not None, f"Invalid NoC0 coordinates: ({noc0_x}, {noc0_y})"
        try:
            self.__write_to_device_reg_unaligned_helper(coord, address, data, dma_threshold)
        except TimeoutDeviceRegisterError:
            raise
        except Exception:
            if self._is_simulation or self._is_mmio_capable:
                raise
            if util.DEBUG_ENABLED:
                util.DEBUG(f"Write failed, retrying via ETH reconfiguration:\n{traceback.format_exc()}")
            self.__configure_working_active_eth()
            self.__write_to_device_reg_unaligned_helper(coord, address, data, dma_threshold)

    def _update_device_after_sigbus(self, new_device: tt_umd.TTDevice):
        # Device was reset, we did new topology discovery, but we want to reuse the same UmdDevice instance to make it easier for users.
        self.__device = new_device
        self._soc_descriptor = tt_umd.SocDescriptor(new_device)

    def __reinit_device_after_sigbus(self):
        # Device was reset, so we need to reinitialize it. Since this probably hit all devices, we do topology discovery again to be safe.
        self.__api._reinit_devices_after_sigbus()

    def noc_read(
        self,
        noc_id: tt_umd.NocId,
        noc0_x: int,
        noc0_y: int,
        address: int,
        buffer: bytearray | memoryview,
        dma_threshold: int,
    ) -> None:
        try:
            """Reads data from address"""
            self.__select_noc_id(noc_id)
            self.__read_from_device_reg_unaligned(noc_id, noc0_x, noc0_y, address, buffer, dma_threshold)
        except tt_umd.SigbusError:
            if util.DEBUG_ENABLED:
                util.DEBUG("Reset detected during noc_read, reinitializing device and retrying...")
            self.__reinit_device_after_sigbus()
            self.noc_read(noc_id, noc0_x, noc0_y, address, buffer, dma_threshold)

    def noc_read_bytes(
        self,
        noc_id: tt_umd.NocId,
        noc0_x: int,
        noc0_y: int,
        address: int,
        size: int,
        dma_threshold: int,
    ) -> bytes:
        """Reads 'size' bytes from address and returns them. Avoid using this method if caller can provide buffer, to save extra copy."""
        buffer = bytearray(size)
        self.noc_read(noc_id, noc0_x, noc0_y, address, buffer, dma_threshold)
        return bytes(buffer)

    def noc_write(
        self,
        noc_id: tt_umd.NocId,
        noc0_x: int,
        noc0_y: int,
        address: int,
        data: bytes | bytearray | memoryview,
        dma_threshold: int,
    ):
        try:
            """Writes data to address"""
            self.__select_noc_id(noc_id)
            self.__write_to_device_reg_unaligned(noc_id, noc0_x, noc0_y, address, data, dma_threshold)
        except tt_umd.SigbusError:
            if util.DEBUG_ENABLED:
                util.DEBUG("Reset detected during noc_write, reinitializing device and retrying...")
            self.__reinit_device_after_sigbus()
            self.noc_write(noc_id, noc0_x, noc0_y, address, data, dma_threshold)

    def bar0_read32(self, address: int) -> int:
        """Reads 4 bytes from PCI address"""
        if not self._is_mmio_capable:
            raise RuntimeError("Device is not mmio capable.")
        try:
            return self.__device.bar_read32(address)
        except tt_umd.SigbusError:
            if util.DEBUG_ENABLED:
                util.DEBUG("Reset detected during bar0_read32, reinitializing device and retrying...")
            self.__reinit_device_after_sigbus()
            return self.__device.bar_read32(address)

    def bar0_write32(self, address: int, data: int):
        """Writes 4 bytes to PCI address"""
        if not self._is_mmio_capable:
            raise RuntimeError("Device is not mmio capable.")
        try:
            self.__device.bar_write32(address, data)
        except tt_umd.SigbusError:
            if util.DEBUG_ENABLED:
                util.DEBUG("Reset detected during bar0_write32, reinitializing device and retrying...")
            self.__reinit_device_after_sigbus()
            self.__device.bar_write32(address, data)

    def convert_from_noc0(self, noc_x: int, noc_y: int, core_type: str, coord_system: str) -> tuple[int, int]:
        """Convert noc0 coordinate into specified coordinate system"""
        core_type_enum = tt_umd.CoreType[core_type.upper()]
        coord_system_enum = tt_umd.CoordSystem[coord_system.upper()]
        core_coord = tt_umd.CoreCoord(noc_x, noc_y, core_type_enum, tt_umd.CoordSystem.NOC0)
        if coord_system_enum == tt_umd.CoordSystem.TRANSLATED:
            output = self._soc_descriptor.translate_chip_coord_to_translated_coord(core_coord)
        else:
            output = self._soc_descriptor.translate_coord_to(core_coord, coord_system_enum)
        return (output.x, output.y)

    def arc_msg(
        self,
        noc_id: tt_umd.NocId,
        msg_code: int,
        wait_for_done: bool,
        args: Sequence[int],
        timeout: datetime.timedelta | float,
    ) -> tuple[int, int, int]:
        try:
            """Send ARC message"""
            self.__select_noc_id(noc_id)
            timeout_ms = timeout.total_seconds() * 1000 if isinstance(timeout, datetime.timedelta) else timeout * 1000
            return self.__device.arc_msg(msg_code, wait_for_done, args, int(timeout_ms))
        except tt_umd.SigbusError:
            if util.DEBUG_ENABLED:
                util.DEBUG("Reset detected during arc_msg, reinitializing device and retrying...")
            self.__reinit_device_after_sigbus()
            return self.arc_msg(noc_id, msg_code, wait_for_done, args, timeout)

    def read_arc_telemetry_entry(self, noc_id: tt_umd.NocId, telemetry_tag: int) -> int:
        """Read ARC telemetry entry"""
        self.__select_noc_id(noc_id)

        def do_read(telemetry_tag: int) -> int:
            arc_telemetry_reader = self.__device.get_arc_telemetry_reader()
            if not arc_telemetry_reader.is_entry_available(telemetry_tag):
                raise RuntimeError(f"Telemetry tag {telemetry_tag} is not available on device {self.device_id}.")
            return arc_telemetry_reader.read_entry(telemetry_tag)

        try:
            return do_read(telemetry_tag)
        except tt_umd.SigbusError:
            if util.DEBUG_ENABLED:
                util.DEBUG("Reset detected during read_arc_telemetry_entry, reinitializing device and retrying...")
            self.__reinit_device_after_sigbus()
            return self.read_arc_telemetry_entry(noc_id, telemetry_tag)
        except Exception:
            if not self._is_mmio_capable:
                raise
            try:
                if util.DEBUG_ENABLED:
                    util.DEBUG(f"Telemetry read failed, retrying via ETH reconfiguration:\n{traceback.format_exc()}")
                # TODO: We should retry only if it was remote read error
                self.__configure_working_active_eth()
                return do_read(telemetry_tag)
            except tt_umd.SigbusError:
                if util.DEBUG_ENABLED:
                    util.DEBUG("Reset detected during read_arc_telemetry_entry, reinitializing device and retrying...")
                self.__reinit_device_after_sigbus()
                return self.read_arc_telemetry_entry(noc_id, telemetry_tag)

    def get_firmware_version(self, noc_id: tt_umd.NocId) -> tt_umd.FirmwareBundleVersion:
        """Returns firmware version"""
        self.__select_noc_id(noc_id)

        def do_read() -> tt_umd.FirmwareBundleVersion:
            firmware_info_provider = self.__device.get_firmware_info_provider()
            return firmware_info_provider.get_firmware_version()

        try:
            firmware_version = do_read()
        except tt_umd.SigbusError:
            if util.DEBUG_ENABLED:
                util.DEBUG("Reset detected during get_firmware_version, reinitializing device and retrying...")
            self.__reinit_device_after_sigbus()
            return self.get_firmware_version(noc_id)
        except Exception:
            if not self._is_mmio_capable:
                raise
            try:
                if util.DEBUG_ENABLED:
                    util.DEBUG(
                        f"Firmware version read failed, retrying via ETH reconfiguration:\n{traceback.format_exc()}"
                    )
                # TODO: We should retry only if it was remote read error
                self.__configure_working_active_eth()
                firmware_version = do_read()
            except tt_umd.SigbusError:
                if util.DEBUG_ENABLED:
                    util.DEBUG("Reset detected during get_firmware_version, reinitializing device and retrying...")
                self.__reinit_device_after_sigbus()
                return self.get_firmware_version(noc_id)
        return firmware_version

    def get_remote_transfer_eth_core(self) -> tuple[int, int] | None:
        """Returns currently active Ethernet core in logical coordinates"""
        remote_communication = self.__device.get_remote_communication()
        if (
            remote_communication is None
        ):  # pyright: ignore[reportUnnecessaryComparison]  # tt_umd stub claims non-Optional but runtime may return None
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

    def get_local_tt_device(self) -> tt_umd.TTDevice:
        if self._is_mmio_capable:
            return self.__device
        remote_communication = self.__device.get_remote_communication()
        return remote_communication.get_local_device()
