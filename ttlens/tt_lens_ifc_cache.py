# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
import atexit
import io
import os
import pickle

from ttlens.tt_lens_ifc_base import TTLensCommunicator
from ttlens import tt_util as util


"""
This module provides a cache for the TTLens interface. It can be used to store the results of device communications,
or load state from the previous run. This is useful when the device is not available.
"""


class TTLensCache(TTLensCommunicator):
    """
    Base caching class that provides cache dictionary and a function to save the cache to a file.
    """

    def __init__(self):
        super().__init__()
        self.cache = {}

    def save(self):
        util.INFO(f"Saving server cache to file {self.filepath}")
        with open(self.filepath, "wb") as f:
            pickle.dump(self.cache, f)
            util.INFO(f"  Saved {len(self.cache)} entries")


class TTLensCacheThrough(TTLensCache):
    """
    A class for caching the return values or device calls. Caching is implemented using a decorator.

    Args:
        communicator (TTLensCommunicator): The interface that contacts the device.
        filepath (str): The path to save the cache file. Default is "ttlens_cache.pkl".
    """

    def __init__(self, communicator, filepath="ttlens_cache.pkl"):
        super().__init__()
        self.communicator = communicator
        self.filepath = filepath

    """
    This class uses a decorator wrapped around the regular interface functions to perform caching.
    """

    def cache_decorator(func):
        def wrapper(self, *args, **kwargs):
            key = (func.__name__, args)
            self.cache[key] = func(self, *args, **kwargs)
            return self.cache[key]

        return wrapper

    def cache_binary_decorator(func):
        def wrapper(self, *args, **kwargs):
            key = (func.__name__, args)
            retval = func(self, *args, **kwargs)
            self.cache[key] = retval.read()
            return retval

        return wrapper

    @cache_decorator
    def pci_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self.communicator.pci_read32(chip_id, noc_x, noc_y, address)

    def pci_write32(self, chip_id, noc_x, noc_y, reg_addr, data):
        return self.communicator.pci_write32(chip_id, noc_x, noc_y, reg_addr, data)

    @cache_decorator
    def pci_read(self, chip_id, x, y, noc_id, reg_addr, size):
        return self.communicator.pci_read(chip_id, x, y, noc_id, reg_addr, size)

    def pci_write(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes):
        return self.communicator.pci_write(chip_id, noc_x, noc_y, address, data)

    @cache_decorator
    def dma_buffer_read32(self, chip_id, dram_addr, dram_chan):
        return self.communicator.dma_buffer_read32(chip_id, dram_addr, dram_chan)

    @cache_decorator
    def pci_read_tile(self, chip_id: int, noc_x: int, noc_y: int, address: int, size: int, data_format: int):
        return self.communicator.pci_read_tile(chip_id, noc_x, noc_y, address, size, data_format)

    @cache_decorator
    def pci_read32_raw(self, chip_id, reg_addr):
        return self.communicator.pci_read32_raw(chip_id, reg_addr)

    def pci_write32_raw(self, chip_id, reg_addr, data):
        return self.communicator.pci_write32_raw(chip_id, reg_addr, data)

    @cache_decorator
    def get_cluster_description(self):
        return self.communicator.get_cluster_description()

    @cache_decorator
    def convert_from_noc0(self, chip_id, noc_x, noc_y, core_type, coord_system):
        return self.communicator.convert_from_noc0(chip_id, noc_x, noc_y, core_type, coord_system)

    @cache_decorator
    def get_device_ids(self):
        return self.communicator.get_device_ids()

    @cache_decorator
    def get_device_arch(self, chip_id):
        return self.communicator.get_device_arch(chip_id)

    @cache_decorator
    def get_device_soc_description(self, chip_id):
        return self.communicator.get_device_soc_description(chip_id)

    @cache_decorator
    def get_file(self, file_path: str) -> str:
        return self.communicator.get_file(file_path)

    @cache_binary_decorator
    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        return self.communicator.get_binary(binary_path)

    @cache_decorator
    def jtag_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self.communicator.jtag_read32(chip_id, noc_x, noc_y, address)

    def jtag_write32(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        return self.communicator.jtag_write32(chip_id, noc_x, noc_y, address, data)

    @cache_decorator
    def jtag_read32_axi(self, chip_id: int, address: int):
        return self.communicator.jtag_read32_axi(chip_id, address)

    def jtag_write32_axi(self, chip_id: int, address: int, data: int):
        return self.communicator.jtag_write32_axi(chip_id, address, data)

    def using_cache(self) -> bool:
        return True


class TTLensCacheReader(TTLensCache):
    """
    A class for reading the cache file. It imitates the high-level interface used to communicate with the device.
    Reading is implemented using a decorator.
    """

    def __init__(self, filepath="ttlens_cache.pkl"):
        super().__init__()
        self.filepath = filepath

        self.load()

    def load(self):
        if os.path.exists(self.filepath):
            util.INFO(f"Loading server cache from file {self.filepath}")
            with open(self.filepath, "rb") as f:
                self.cache = pickle.load(f)
                util.INFO(f"  Loaded {len(self.cache)} entries")
        else:
            util.ERROR(f"Cache file {self.filepath} does not exist")

    """
    The decorator performs all the work of reading from the cache. The functions just provide the correct interface.
    """

    def read_decorator(func):
        def wrapper(self, *args, **kwargs):
            key = (func.__name__, args)

            if key not in self.cache:
                util.ERROR(f"Cache miss for {func.__name__}.")
                raise util.TTException(f"Cache miss for {func.__name__}.")

            return self.cache[key]

        return wrapper

    def read_cached_binary_decorator(func):
        def wrapper(self, *args, **kwargs):
            key = (func.__name__, args)

            if key not in self.cache:
                util.ERROR(f"Cache miss for {func.__name__}.")
                raise util.TTException(f"Cache miss for {func.__name__}.")

            return io.BytesIO(self.cache[key])

        return wrapper

    @read_decorator
    def pci_read32(self, chip_id, noc_x, noc_y, reg_addr):
        pass

    def pci_write32(self, chip_id, noc_x, noc_y, reg_addr, data):
        raise util.TTException("Device not available, cannot write to cache.")

    @read_decorator
    def pci_read(self, chip_id, noc_x, noc_y, reg_addr, size):
        pass

    def pci_write(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: bytes):
        raise util.TTException("Device not available, cannot write to cache.")

    @read_decorator
    def dma_buffer_read32(self, chip_id, dram_addr, dram_chan):
        pass

    @read_decorator
    def pci_read_tile(self, chip_id, x, y, z, reg_addr, msg_size, data_format):
        pass

    @read_decorator
    def pci_read32_raw(self, chip_id, reg_addr):
        pass

    def pci_write32_raw(self, chip_id, reg_addr, data):
        raise util.TTException("Device not available, cannot write to cache.")

    @read_decorator
    def get_cluster_description(self):
        pass

    @read_decorator
    def convert_from_noc0(self, chip_id, noc_x, noc_y, core_type, coord_system):
        pass

    @read_decorator
    def get_device_ids(self):
        pass

    @read_decorator
    def get_device_arch(self, chip_id):
        pass

    @read_decorator
    def get_device_soc_description(self, chip_id):
        pass

    @read_decorator
    def get_file(self, file_path: str) -> str:
        pass

    @read_cached_binary_decorator
    def get_binary(self, binary_path: str) -> io.BufferedIOBase:
        pass

    @read_decorator
    def jtag_read32(self, chip_id: int, noc_x: int, noc_y: int, address: int):
        return self.communicator.jtag_read32(chip_id, noc_x, noc_y, address)

    def jtag_write32(self, chip_id: int, noc_x: int, noc_y: int, address: int, data: int):
        return self.communicator.jtag_write32(chip_id, noc_x, noc_y, address, data)

    @read_decorator
    def jtag_read32_axi(self, chip_id: int, address: int):
        return self.communicator.jtag_read32_axi(chip_id, address)

    def jtag_write32_axi(self, chip_id: int, address: int, data: int):
        return self.communicator.jtag_write32_axi(chip_id, address, data)

    def using_cache(self) -> bool:
        return True


def init_cache_writer(original_communicator, filepath="ttlens_cache.pkl"):
    communicator = TTLensCacheThrough(original_communicator, filepath)
    atexit.register(communicator.save)
    return communicator


def init_cache_reader(filepath="ttlens_cache.pkl"):
    communicator = TTLensCacheReader(filepath)
    return communicator
