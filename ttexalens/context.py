# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from functools import cached_property
from sortedcontainers import SortedSet
from typing import Iterable, TYPE_CHECKING
import tt_umd

from ttexalens.coordinate import OnChipCoordinate
from ttexalens import util as util
from ttexalens.firmware import ELF


if TYPE_CHECKING:
    from ttexalens.command_parser import CommandMetadata
    from ttexalens.device import Device
    from ttexalens.hardware.risc_debug import RiscLocation
    from ttexalens.server import FileAccessApi
    from ttexalens.umd_api import UmdApi

# All-encompassing structure representing a TTExaLens context
class Context:
    def __init__(
        self,
        umd_api: UmdApi,
        file_api: FileAccessApi,
        short_name: str = "default",
        use_noc1=False,
        use_4B_mode=True,
        dma_read_threshold: int = 24,  # Measured thresholds for DMA vs NOC transfers on WH
        dma_write_threshold: int = 56,  # Measured thresholds for DMA vs NOC transfers on WH
        noc_failover: bool = True,
    ):
        self.umd_api = umd_api
        self.file_api = file_api
        self.short_name = short_name
        self.use_noc1 = use_noc1
        self.use_4B_mode: bool = use_4B_mode
        self.dma_read_threshold: int = dma_read_threshold
        self.dma_write_threshold: int = dma_write_threshold
        self.noc_failover = noc_failover

        self.commands: list[CommandMetadata] = []
        self.loaded_elfs: dict[RiscLocation, str] = {}

    def assign_commands(self, commands: list[CommandMetadata]):
        self.commands = []
        for cmd in commands:
            if cmd.context is None or self.short_name in cmd.context or "util" in cmd.context:
                self.commands.append(cmd)

    @cached_property
    def devices(self) -> dict[int, Device]:
        from ttexalens.device import Device

        device_ids = self.device_ids
        devices: dict[int, Device] = dict()
        for device_id in device_ids:
            util.DEBUG(f"Loading device {device_id}")
            devices[device_id] = Device.create(device_id, self)
        return devices

    @cached_property
    def cluster_descriptor(self) -> tt_umd.ClusterDescriptor:
        return self.umd_api.get_cluster_descriptor()

    @cached_property
    def device_ids(self) -> SortedSet[int]:
        device_ids: Iterable[int]
        try:
            device_ids = self.cluster_descriptor.get_all_chips()
        except:
            device_ids = []
        return SortedSet(d for d in device_ids)

    @cached_property
    def device_by_unique_id(self) -> dict[int, Device]:
        return {device.unique_id: device for device in self.devices.values()}

    @cached_property
    def elf(self):
        return ELF(self.file_api, {}, None)

    def find_device_by_id(self, device_id: int) -> Device:
        device = self.devices.get(device_id, None)
        if not device:
            device = self.device_by_unique_id.get(device_id, None)
        if not device:
            raise util.TTException(f"Invalid device_id {device_id}.")
        return device

    def get_risc_elf_path(self, risc_location: RiscLocation) -> str | None:
        return self.loaded_elfs.get(risc_location)

    def elf_loaded(self, risc_location: RiscLocation, elf_path: str):
        self.loaded_elfs[risc_location] = elf_path

    def convert_loc_to_umd(self, location: OnChipCoordinate) -> tuple[int, int]:
        return location._noc0_coord
