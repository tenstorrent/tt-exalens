# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from ttexalens.hardware.device_address import DeviceAddress


class MemoryBlock:
    def __init__(self, size: int, address: DeviceAddress):
        self.size = size
        self.address = address
