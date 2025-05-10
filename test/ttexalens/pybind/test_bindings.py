# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

import unittest
import sys
import os

from typing import Union

ttexalens_pybind_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../build/lib"))
sys.path.append(ttexalens_pybind_path)

if not os.path.isfile(os.path.join(ttexalens_pybind_path, "ttexalens_pybind.so")):
    print(f"Error: 'ttexalens_pybind.so' not found in {ttexalens_pybind_path}. Try: make build")
    sys.exit(1)

if not os.path.isfile(os.path.join(ttexalens_pybind_path, "ttexalens_pybind_unit_tests.so")):
    print(f"Error: 'ttexalens_pybind_unit_tests.so' not found in {ttexalens_pybind_path}. Try: make build")
    sys.exit(1)

import ttexalens_pybind as pb
from ttexalens_pybind_unit_tests import set_ttexalens_test_implementation


class TestBindings(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        set_ttexalens_test_implementation()
        super().__init__(methodName)

    def test_pci_read_write32(
        self,
        data: int = 2,
    ):
        assert pb.pci_read32(0, 0, 1, 0, 0) is None, "Error: pci_read32 should return None before writing."
        assert pb.pci_write32(0, 0, 1, 0, 0, data) == data, "Error: pci_write32 should return the data written."
        assert pb.pci_read32(0, 0, 1, 0, 0) == data, "Error: pci_read32 should return the data written."

    def test_pci_read_write32_raw(
        self,
        data: int = 4,
    ):
        assert pb.pci_read32_raw(1, 1) is None, "Error: pci_read32_raw should return None before writing."
        assert pb.pci_write32_raw(1, 1, data) == data, "Error: pci_write32_raw should return the data written."
        assert pb.pci_read32_raw(1, 1) == data, "Error: pci_read32_raw should return the data written."

    def test_pci_read_write(self, data: Union[bytes, bytearray] = bytearray([1, 5, 3]), size=3):
        assert pb.pci_read(0, 3, 3, 3, 3, size) is None, "Error: pci_read should return None before writing."
        assert (
            pb.pci_write(0, 3, 3, 3, 3, data, 3) == size
        ), "Error: pci_write should return the size of the data written."

        rlist = pb.pci_read(0, 3, 3, 3, 3, 3)
        for x, y in zip(data, rlist):
            assert x == y, "Error: pci_read should return the data written."

    def pci_write_negative(self, data: list = [1, 2, -3], size=3):
        assert (
            pb.pci_write(0, 5, 5, 5, 5, data, 3) is None
        ), "Error: pci_write should return None if any of the data is negative."
        pb.pci_write(0, 5, 5, 5, 5, [4, 5, 6], 3)
        rlist = pb.pci_read(0, 5, 5, 5, 5, 3)
        for x, y in zip(data, rlist):
            assert x == y, "Error: pci_read should return the data written."

    def test_dma_buffer_read32(self, data: int = 5, channel: int = 32):
        assert (
            pb.dma_buffer_read32(2, 1, channel) is None
        ), "Error: dma_buffer_read32 should return None before writing."
        pb.pci_write32_raw(2, 1, data)
        assert (
            pb.dma_buffer_read32(2, 1, channel) == data + channel
        ), "Error: dma_buffer_read32 should return the data written plus channel used for reading."

    def test_pci_read_tile(self):
        assert (
            pb.pci_read_tile(0, 1, 2, 3, 4, 5, 6) == "pci_read_tile(0, 1, 2, 3, 4, 5, 6)"
        ), "Error: pci_read_tile(0, 1, 2, 3, 4, 5, 6) should return 'pci_read_tile(0, 1, 2, 3, 4, 5, 6)'."

    def test_get_cluster_description(self):
        assert (
            pb.get_cluster_description() == "get_cluster_description()"
        ), "Error: get_cluster_description() should return 'get_cluster_description()'."

    def test_get_device_ids(self):
        assert pb.get_device_ids() == [0, 1], "Error: get_device_ids() should return [0, 1]."

    def test_get_device_arch(self, id: int = 3):
        assert pb.get_device_arch(id) == "get_device_arch(" + str(id) + ")", (
            "Error: get_device_arch() should return 'get_device_arch(" + str(id) + ")'."
        )

    def test_get_device_soc_description(self, id: int = 5):
        assert pb.get_device_soc_description(id) == "get_device_soc_description(" + str(id) + ")", (
            "Error: get_device_soc_description() should return 'get_device_soc_description(" + str(id) + ")'."
        )

    def test_convert_from_noc0(self):
        assert pb.convert_from_noc0(1, 2, 3, "core_type", "coord_system") == (
            3,
            4,
        ), "Error: convert_from_noc0() should return (3, 4)."


if __name__ == "__main__":
    unittest.main()
