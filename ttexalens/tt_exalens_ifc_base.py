# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod
import io
from typing import Iterable, List, Tuple


class TTExaLensCommunicator(ABC):
    """
    Base class for the TTExaLens interfaces. It defines the high-level methods that must be implemented for TTExaLens to
    communicate with the target device. They are later derived to communicate with server, use pybind or read from cache.
    """

    @abstractmethod
    def pci_read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int) -> int:
        pass

    @abstractmethod
    def pci_write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int) -> int:
        pass

    @abstractmethod
    def pci_read(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, size: int) -> bytes:
        pass

    @abstractmethod
    def pci_write(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes) -> int:
        pass

    @abstractmethod
    def pci_read32_raw(self, chip_id: int, address: int) -> int:
        pass

    @abstractmethod
    def pci_write32_raw(self, chip_id: int, address: int, data: int) -> int:
        pass

    @abstractmethod
    def dma_buffer_read32(self, chip_id: int, address: int, channel: int) -> int:
        pass

    @abstractmethod
    def pci_read_tile(
        self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, size: int, data_format: int
    ) -> str:
        pass

    @abstractmethod
    def get_cluster_description(self) -> str:
        pass

    @abstractmethod
    def convert_from_noc0(self, chip_id, noc_x, noc_y, core_type, coord_system) -> Tuple[int, int]:
        pass

    @abstractmethod
    def get_device_ids(self) -> Iterable[int]:
        pass

    @abstractmethod
    def get_device_arch(self, chip_id: int) -> str:
        pass

    @abstractmethod
    def get_device_soc_description(self, chip_id: int) -> str:
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> str:
        pass

    @abstractmethod
    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        pass

    @abstractmethod
    def jtag_read32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int) -> int:
        pass

    @abstractmethod
    def jtag_write32(self, noc_id: int, chip_id: int, noc_x: int, noc_y: int, address: int, data: int) -> int:
        pass

    @abstractmethod
    def jtag_read32_axi(self, chip_id: int, address: int) -> int:
        pass

    @abstractmethod
    def jtag_write32_axi(self, chip_id: int, address: int, data: int) -> int:
        pass

    @abstractmethod
    def arc_msg(
        self, noc_id: int, device_id: int, msg_code: int, wait_for_done: bool, arg0: int, arg1: int, timeout: int
    ) -> List[int]:
        pass

    @abstractmethod
    def read_arc_telemetry_entry(self, device_id: int, telemetry_tag: int) -> int:
        pass

    def using_cache(self) -> bool:
        return False
