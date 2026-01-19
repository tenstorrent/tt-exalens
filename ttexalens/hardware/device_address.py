# SPDX-FileCopyrightText: © 2025 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass


@dataclass
class DeviceAddress:
    private_address: int | None = None
    noc_address: int | None = None
    bar0_address: int | None = None
    noc_id: int | None = None

    def __post_init__(self):
        assert (
            self.private_address is not None or self.noc_address is not None or self.bar0_address is not None
        ), "Either private_address or noc_address or bar0_address must be set"
