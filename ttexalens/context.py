# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from abc import abstractmethod
from functools import cached_property
from typing import Dict, Optional, Set
from ttexalens.coordinate import OnChipCoordinate
from ttexalens import util as util
from ttexalens.firmware import ELF

# All-encompassing structure representing a TTExaLens context
class Context:
    def __init__(self, server_ifc, cluster_desc, short_name, use_noc1=False):
        self.server_ifc = server_ifc
        self._cluster_desc = cluster_desc
        self.short_name = short_name
        self.use_noc1 = use_noc1

    def filter_commands(self, commands):
        self.commands = []
        for cmd in commands:
            if self.short_name in cmd["context"] or cmd["context"] == "util":
                self.commands.append(cmd)

    @cached_property
    def devices(self):
        from ttexalens import device

        device_ids = self.device_ids
        devices: Dict[int, device.Device] = dict()
        for device_id in device_ids:
            device_desc_path = self.server_ifc.get_device_soc_description(device_id)
            util.DEBUG(f"Loading device {device_id} from {device_desc_path}")
            devices[device_id] = device.Device.create(
                self.arch,
                device_id=device_id,
                cluster_desc=self.cluster_desc.root,
                device_desc_path=device_desc_path,
                context=self,
            )
        return devices

    @cached_property
    def cluster_desc(self):
        return self._cluster_desc

    @cached_property
    def device_ids(self) -> Set[int]:
        try:
            device_ids = self.server_ifc.get_device_ids()
            return util.set(d for d in device_ids)
        except:
            return None

    @cached_property
    def arch(self):
        try:
            return self.server_ifc.get_device_arch(min(self.device_ids))
        except:
            return None

    @property
    @abstractmethod
    def elf(self):
        raise util.TTException(f"We are running with limited functionality, elf files are not available.")

    @abstractmethod
    def get_risc_elf_path(self, location: OnChipCoordinate, risc_id: int) -> Optional[str]:
        pass

    def elf_loaded(self, location: OnChipCoordinate, risc_id: int, elf_path: str):
        pass

    def convert_loc_to_umd(self, location: OnChipCoordinate):
        if not self.use_noc1:
            return location.to("virtual")
        else:
            coord = location.to("noc1")
            fake_noc0 = OnChipCoordinate(coord[0], coord[1], "noc0", location._device)
            result = fake_noc0.to("virtual")
            return result

    def __repr__(self):
        return f"context"


class LimitedContext(Context):
    def __init__(self, server_ifc, cluster_desc_yaml, use_noc1=False):
        super().__init__(server_ifc, cluster_desc_yaml, "limited", use_noc1)
        self.loaded_elfs = {}  # (OnChipCoordinate, risc_id) => elf_path

    def get_risc_elf_path(self, location: OnChipCoordinate, risc_id: int) -> Optional[str]:
        return self.loaded_elfs.get((location, risc_id))

    def elf_loaded(self, location: OnChipCoordinate, risc_id: int, elf_path: str):
        self.loaded_elfs[(location, risc_id)] = elf_path

    @cached_property
    def elf(self):
        return ELF(self.server_ifc, {}, None)

    def __repr__(self):
        return f"LimitedContext"


# TODO: We should implement support for Metal
class MetalContext(Context):
    def __init__(self, server_ifc, cluster_desc_yaml):
        super().__init__(server_ifc, cluster_desc_yaml, "metal")

    def __repr__(self):
        return f"MetalContext"
