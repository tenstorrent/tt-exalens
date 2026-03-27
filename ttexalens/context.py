# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations
from dataclasses import dataclass, field
from functools import cached_property
import traceback
from typing import Iterable, TYPE_CHECKING

from sortedcontainers import SortedSet
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

@dataclass(eq=False)
class HardwareSession:
    """Owns the live connection to hardware and all configuration that governs
    how memory is accessed. Can be constructed without FileAccessApi.
    """

    umd_api: "UmdApi"
    use_4B_mode: bool = True
    dma_read_threshold: int = 0
    dma_write_threshold: int = 0
    noc_failover: bool = True
    safe_mode: bool = False
    short_name: str = "default"

    # Backing field for the use_noc1 managed property.
    # Must be named _use_noc1 and excluded from __init__ — a dataclass field and a
    # @property cannot share the same name; the property descriptor would be overwritten.
    _use_noc1: bool = field(default=False, init=False, repr=False)

    @property
    def use_noc1(self) -> bool:
        return self._use_noc1

    @use_noc1.setter
    def use_noc1(self, value: bool) -> None:
        if value == self._use_noc1:
            return
        self._use_noc1 = value
        # Only propagate if devices have already been cached.
        # Using "devices" in self.__dict__ avoids triggering the lazy device load
        # when use_noc1 is set before any device has been accessed.
        if "devices" in self.__dict__:
            for device in self.devices.values():
                device.switch_noc(int(value))

    @cached_property
    def devices(self) -> "dict[int, Device]":
        from ttexalens.device import Device
        device_ids = self.device_ids
        devices: dict[int, Device] = dict()
        for device_id in device_ids:
            util.DEBUG(f"Loading device {device_id}")
            devices[device_id] = Device.create(device_id, self)
        return devices

    @cached_property
    def device_ids(self) -> SortedSet:
        device_ids: Iterable[int]
        try:
            device_ids = self.cluster_descriptor.get_all_chips()
        except Exception:
            util.DEBUG(f"Could not get device IDs from cluster descriptor:\n{traceback.format_exc()}")
            device_ids = []
        return SortedSet(d for d in device_ids)

    @cached_property
    def device_by_unique_id(self) -> "dict[int, Device]":
        return {device.unique_id: device for device in self.devices.values()}

    @cached_property
    def cluster_descriptor(self) -> "tt_umd.ClusterDescriptor":
        return self.umd_api.get_cluster_descriptor()

    def get_device(self, device_id: int):
        """Thin delegation to umd_api.get_device(). Provides a seam for mocking."""
        return self.umd_api.get_device(device_id)

    def find_device_by_id(self, device_id: int):
        """Look up by logical id first, then by unique id."""
        device = self.devices.get(device_id, None)
        if not device:
            device = self.device_by_unique_id.get(device_id, None)
        if not device:
            raise util.TTException(f"Invalid device_id {device_id}.")
        return device

    def convert_loc_to_umd(self, location: "OnChipCoordinate") -> tuple[int, int]:
        return location._noc0_coord

    @classmethod
    def from_api(cls, umd_api: "UmdApi", **kwargs) -> "HardwareSession":
        """Factory. The only intended constructor path for this sprint.
        Accepts any UmdApi including mocks.
        """
        session = cls(umd_api=umd_api, **{
            k: v for k, v in kwargs.items() if k != "use_noc1"
        })
        session.use_noc1 = kwargs.get("use_noc1", False)
        return session


@dataclass(eq=False)
class DebugSession:
    """Composes a HardwareSession with FileAccessApi to add ELF and symbol capabilities."""

    hardware: HardwareSession
    file_api: "FileAccessApi"

    # Must be declared with field(default_factory=dict, init=False) so it is not a
    # required constructor argument and is initialized before __post_init__ runs.
    _loaded_elfs: dict = field(default_factory=dict, init=False, repr=False)

    @cached_property
    def elf(self):
        return ELF(self.file_api, {}, None)

    def get_risc_elf_path(self, risc_location: "RiscLocation") -> "str | None":
        return self._loaded_elfs.get(risc_location)

    def elf_loaded(self, risc_location: "RiscLocation", elf_path: str) -> None:
        """Two-argument setter — stores elf_path. NOT a predicate."""
        self._loaded_elfs[risc_location] = elf_path

    # --- Proxy properties delegating to self.hardware ---
    # Must be plain @property, NOT @cached_property — using @cached_property would
    # create an independent cache on DebugSession that diverges from HardwareSession.

    @property
    def devices(self) -> "dict[int, Device]":
        return self.hardware.devices

    @property
    def use_noc1(self) -> bool:
        return self.hardware.use_noc1

    @use_noc1.setter
    def use_noc1(self, value: bool) -> None:
        # ONLY delegate — no switch_noc() logic here.
        # All propagation logic lives on HardwareSession.use_noc1.setter.
        self.hardware.use_noc1 = value

    @property
    def safe_mode(self) -> bool:
        return self.hardware.safe_mode

    @safe_mode.setter
    def safe_mode(self, value: bool) -> None:
        self.hardware.safe_mode = value

    @property
    def device_ids(self):
        return self.hardware.device_ids

    @property
    def cluster_descriptor(self):
        return self.hardware.cluster_descriptor

    @property
    def short_name(self) -> str:
        return self.hardware.short_name

    def find_device_by_id(self, device_id: int):
        return self.hardware.find_device_by_id(device_id)

    @property
    def device_by_unique_id(self) -> "dict[int, Device]":
        return self.hardware.device_by_unique_id

    def convert_loc_to_umd(self, location: "OnChipCoordinate") -> tuple[int, int]:
        return self.hardware.convert_loc_to_umd(location)


# Context must NOT be decorated with @dataclass.
# DebugSession is a dataclass. If Context were also a dataclass, Python would generate
# an __init__ that replaces the hand-written flat constructor, breaking all 40+ call sites.
class Context(DebugSession):
    """Backward-compatible entry point. Inherits DebugSession.
    isinstance(context, DebugSession) is True for all locally-constructed Context instances.
    """

    def __init__(
        self,
        umd_api: "UmdApi",
        file_api: "FileAccessApi",
        short_name: str = "default",
        use_noc1=False,
        use_4B_mode=True,
        dma_read_threshold: int = 24,  # Measured thresholds for DMA vs NOC transfers on WH
        dma_write_threshold: int = 56,  # Measured thresholds for DMA vs NOC transfers on WH
        noc_failover: bool = True,
        safe_mode: bool = True,  # Prevents potentially unsafe operations (e.g., writing to certain memory regions) without explicit overrides
    ):
        hardware = HardwareSession(
            umd_api=umd_api,
            use_4B_mode=use_4B_mode,
            dma_read_threshold=dma_read_threshold,
            dma_write_threshold=dma_write_threshold,
            noc_failover=noc_failover,
            safe_mode=safe_mode,
            short_name=short_name,
        )
        # Must call super().__init__(), not object.__setattr__(), so that DebugSession's
        # dataclass __init__ runs correctly and _loaded_elfs is initialized.
        super().__init__(hardware=hardware, file_api=file_api)
        # Set use_noc1 after super().__init__() so the property setter can fire.
        self.hardware.use_noc1 = use_noc1

        self.commands: list = []

    def assign_commands(self, commands: "list[CommandMetadata]"):
        self.commands = []
        for cmd in commands:
            if cmd.context is None or self.short_name in cmd.context or "util" in cmd.context:
                self.commands.append(cmd)

    # --- Backward-compat property aliases ---

    @property
    def umd_api(self) -> "UmdApi":
        """Read-only alias. Context.umd_api used to be a plain instance attribute;
        now it delegates to hardware."""
        return self.hardware.umd_api

    @property
    def use_4B_mode(self) -> bool:
        return self.hardware.use_4B_mode

    @use_4B_mode.setter
    def use_4B_mode(self, value: bool) -> None:
        # Write site: cli_commands/go.py:48
        self.hardware.use_4B_mode = value

    @property
    def safe_mode(self) -> bool:
        return self.hardware.safe_mode

    @safe_mode.setter
    def safe_mode(self, value: bool) -> None:
        # Write sites: test_lib.py:790 and :795
        self.hardware.safe_mode = value

    @property
    def dma_read_threshold(self):
        return self.hardware.dma_read_threshold

    @property
    def dma_write_threshold(self):
        return self.hardware.dma_write_threshold

    @property
    def noc_failover(self):
        return self.hardware.noc_failover

    @property
    def loaded_elfs(self) -> dict:
        # Must return self._loaded_elfs (owned by DebugSession), NOT a new dict.
        # If this were a plain instance attribute assigned in Context.__init__,
        # context.elf_loaded() (which writes DebugSession._loaded_elfs) and
        # context.loaded_elfs (which reads here) would silently diverge.
        return self._loaded_elfs

    # NOTE: short_name and use_noc1 are NOT re-declared on Context.
    # They are inherited from DebugSession.short_name and DebugSession.use_noc1.
    # Re-declaring them would shadow the DebugSession proxies and create duplicate logic.
