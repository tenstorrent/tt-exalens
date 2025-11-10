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

    def translate_private_to_noc_address(self, address: int) -> int | None:
        if self.address.private_address is None or self.address.noc_address is None:
            return None
        if not self.contains_private_address(address):
            return None
        return self.address.noc_address + (address - self.address.private_address)
