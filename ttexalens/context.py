# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from abc import abstractmethod
from functools import cached_property
from typing import Iterable, TYPE_CHECKING
from ttexalens.coordinate import OnChipCoordinate
from ttexalens import util as util
from ttexalens.firmware import ELF
from sortedcontainers import SortedSet

from ttexalens.hardware.risc_debug import RiscLocation
from ttexalens.hardware.risc_debug import RiscLocation

if TYPE_CHECKING:
    from ttexalens.device import Device
    from ttexalens.command_parser import CommandMetadata
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
    ):
        self.umd_api = umd_api
        self.file_api = file_api
        self.short_name = short_name
        self.use_noc1 = use_noc1
        self.use_4B_mode: bool = use_4B_mode
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
            device_desc_path = self.umd_api.get_device_soc_description(device_id)
            util.DEBUG(f"Loading device {device_id} from {device_desc_path}")
            devices[device_id] = Device.create(
                self.arch,
                device_id=device_id,
                cluster_descriptor=self.cluster_descriptor,
                device_desc_path=device_desc_path,
                context=self,
            )
        return devices

    @cached_property
    def cluster_descriptor(self):
        return self.umd_api.get_cluster_description()

    @cached_property
    def device_ids(self) -> SortedSet[int]:
        device_ids: Iterable[int]
        try:
            device_ids = self.umd_api.get_device_ids()
        except:
            device_ids = []
        return SortedSet(d for d in device_ids)

    @cached_property
    def arch(self):
        try:
            return self.umd_api.get_device_arch(min(self.device_ids))
        except:
            return None

    @cached_property
    def elf(self):
        return ELF(self.file_api, {}, None)

    def get_risc_elf_path(self, risc_location: RiscLocation) -> str | None:
        return self.loaded_elfs.get(risc_location)

    def elf_loaded(self, risc_location: RiscLocation, elf_path: str):
        self.loaded_elfs[risc_location] = elf_path

    def convert_loc_to_umd(self, location: OnChipCoordinate) -> tuple[int, int]:
        return location._noc0_coord
