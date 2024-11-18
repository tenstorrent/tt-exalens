# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod
import io


class DbdCommunicator(ABC):
    """
    Base class for the TTLens interfaces. It defines the high-level methods that must be implemented for TTLens to
    communicate with the target device. They are later derived to communicate with server, use pybind or read from cache.
    """
    @abstractmethod
    def pci_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        pass

    @abstractmethod
    def pci_write32(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        pass

    @abstractmethod
    def pci_read(self, chip_id: int, noc_x: int, noc_y: int, address: int, size: int):
        pass

    @abstractmethod
    def pci_write(
        self, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes
    ):
        pass

    @abstractmethod
    def pci_read32_raw(self, chip_id: int, address: int):
        pass

    @abstractmethod
    def pci_write32_raw(self, chip_id: int, address: int, data: int):
        pass

    @abstractmethod
    def dma_buffer_read32(self, chip_id: int, address: int, channel: int):
        pass

    @abstractmethod
    def pci_read_tile(self, chip_id: int, noc_x: int, noc_y: int, address: int, size: int, data_format: int):
        pass

    @abstractmethod
    def get_runtime_data(self):
        pass

    @abstractmethod
    def get_cluster_description(self):
        pass

    @abstractmethod
    def get_harvester_coordinate_translation(self, chip_id: int):
        pass

    @abstractmethod
    def get_device_ids(self):
        pass

    @abstractmethod
    def get_device_arch(self, chip_id: int):
        pass

    @abstractmethod
    def get_device_soc_description(self, chip_id: int):
        pass

    @abstractmethod
    def get_file(self, file_path: str) -> str:
        pass

    @abstractmethod
    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        pass

    @abstractmethod
    def get_run_dirpath(self) -> str:
        pass

    @abstractmethod
    def jtag_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        pass

    @abstractmethod
    def jtag_write32(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        pass

    @abstractmethod
    def jtag_read32_axi(self, chip_id: int, address: int):
        pass

    @abstractmethod
    def jtag_write32_axi(self, chip_id: int, address: int, data: int):
        pass
    
    def using_cache(self) -> bool:
        return False
