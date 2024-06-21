# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from abc import ABC, abstractmethod
import shutil
import os
import io


class DbdCommunicator(ABC):
    """
    Base class for the debuda interfaces. It defines the high-level methods that must be implemented for debuda to
    communicate with the target device. They are later derived to communicate with server, use pybind or read from cache.
    """
    def __init__(self):
        self._tmp_folder = '/tmp/debuda'
        if os.path.exists(self._tmp_folder):
            shutil.rmtree(self._tmp_folder)
            os.mkdir(self._tmp_folder)

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
    def get_file(self, file_path: str):
        pass

    @abstractmethod
    def get_binary(self, binary_path: str):
        pass

    @abstractmethod
    def get_run_dirpath(self):
        pass
    
    def save_tmp_file(self, filename: str, content, mode='wb'):
        filename = os.path.join(self._tmp_folder, os.path.basename(filename))
        with open(filename, mode) as f:
            if isinstance(content, io.BytesIO):
                f.write(content.getbuffer())
            else:
                f.write(content)
        return filename

    def using_cache(self):
        return False
