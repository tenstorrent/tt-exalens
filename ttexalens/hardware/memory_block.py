# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.device_address import DeviceAddress


class MemoryBlock:
    def __init__(self, size: int, address: DeviceAddress):
        self.size = size
        self.address = address

    def contains_private_address(self, address: int) -> bool:
        assert self.address.private_address is not None
        return address >= self.address.private_address and address < self.address.private_address + self.size

    def contains_noc_address(self, address: int) -> bool:
        assert self.address.noc_address is not None
        return address >= self.address.noc_address and address < self.address.noc_address + self.size

    def translate_to_noc_address(self, address: int) -> int | None:
        if self.address.noc_address is None:
            return None
        if self.contains_noc_address(address):
            return address
        if self.address.private_address is None:
            return None
        if not self.contains_private_address(address):
            return None
        return self.address.noc_address + (address - self.address.private_address)

    def exposed_through_noc(self) -> bool:
        return self.address.noc_address is not None
