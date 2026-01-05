# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from dataclasses import dataclass
import datetime
from functools import cache, cached_property
import tt_umd
from typing import Iterable, Sequence

from tabulate import tabulate
from ttexalens.context import Context
from ttexalens.coordinate import CoordinateTranslationError, OnChipCoordinate
from ttexalens.hardware.arc_block import ArcBlock
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.hardware.tensix_registers_description import TensixDebugBusDescription, TensixRegisterDescription
from ttexalens.object import TTObject
from ttexalens.umd_device import UmdDevice
from ttexalens import util as util


class TensixInstructions:
    def __init__(self, ops):
        for func_name in dir(ops):
            func = getattr(ops, func_name)
            if callable(func):
                static_method = staticmethod(func)
                setattr(self.__class__, func_name, static_method)

    @staticmethod
    def TT_OP_SFPLOAD(lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr):
        pass

    @staticmethod
    def TT_OP_STALLWAIT(stall_res, wait_res):
        pass

    @staticmethod
    def TT_OP_MOVDBGA2D(dest_32b_lo, src, addr_mode, instr_mod, dst):
        pass

    @staticmethod
    def TT_OP_SFPSTORE(lreg_ind, instr_mod0, sfpu_addr_mode, dest_reg_addr):
        pass

    @staticmethod
    def TT_OP_SETRWC(clear_ab_vld, rwc_cr, rwc_d, rwc_b, rwc_a, BitMask):
        pass

    @staticmethod
    def TT_OP_ZEROACC(clear_mode, AddrMode, dst):
        pass

    @staticmethod
    def TT_OP_SFPSHFT(Imm12, VC, VD, Mod1):
        pass

    @staticmethod
    def TT_OP_INCRWC(cr, DstInc, SrcBInc, SrcAInc):
        pass


#
# Device class: generic API for talking to specific devices. This class is the parent of specific
# device classes (e.g. WormholeDevice, BlackholeDevice). The create class method is used to create
# a specific device.
#
class Device(TTObject):
    instructions: TensixInstructions
    DIE_X_TO_NOC_0_X: list[int] = []
    DIE_Y_TO_NOC_0_Y: list[int] = []
    NOC_0_X_TO_DIE_X: list[int] = []
    NOC_0_Y_TO_DIE_Y: list[int] = []

    # NOC reg type
    class RegType:
        Cmd = 0
        Config = 1
        Status = 2

    @cached_property
    def debuggable_cores(self):
        block_types_with_cores = ["functional_workers", "eth"]
        cores: list[RiscDebug] = []
        for block_type in block_types_with_cores:
            for noc_block in self.get_blocks(block_type):
                cores.extend(noc_block.debuggable_riscs)
        return cores

    def is_wormhole(self) -> bool:
        return False

    def is_blackhole(self) -> bool:
        return False

    def is_quasar(self) -> bool:
        return False

    # Class method to create a Device object given device architecture
    @staticmethod
    def create(device_id: int, context: Context):
        umd_device = context.umd_api.get_device(device_id)
        arch = umd_device.arch
        match arch:
            case tt_umd.ARCH.WORMHOLE_B0:
                from ttexalens.hw.tensix.wormhole import wormhole

                return wormhole.WormholeDevice(device_id, umd_device, context)

            case tt_umd.ARCH.BLACKHOLE:
                from ttexalens.hw.tensix.blackhole import blackhole

                return blackhole.BlackholeDevice(device_id, umd_device, context)

            case tt_umd.ARCH.QUASAR:
                from ttexalens.hw.tensix.quasar import quasar

                return quasar.QuasarDevice(device_id, umd_device, context)

            case _:
                raise RuntimeError(f"Architecture {arch} is not supported")

    def __init__(self, id: int, umd_device: UmdDevice, context: Context):
        self._id: int = id
        self._arch = umd_device.arch
        self._context = context
        self._umd_device = umd_device
        self._soc_descriptor = umd_device.soc_descriptor
        self._has_mmio = umd_device.is_mmio_capable
        self._has_jtag = umd_device.is_jtag_capable
        self._init_coordinate_systems()
        self.unique_id = umd_device.unique_id

    @cached_property
    def firmware_version(self):
        noc_id = 1 if self._context.use_noc1 else 0
        fw = self._umd_device.get_firmware_version(noc_id)
        return util.FirmwareVersion(fw.major, fw.minor, fw.patch)

    def noc_read(
        self,
        location: OnChipCoordinate,
        address: int,
        size_bytes: int,
        noc_id: int | None = None,
        use_4B_mode: bool | None = None,
    ) -> bytes:
        noc_x, noc_y = location._noc0_coord
        if noc_id is None:
            noc_id = 1 if self._context.use_noc1 else 0
        if use_4B_mode is None:
            use_4B_mode = self._context.use_4B_mode
        return self._umd_device.noc_read(noc_id, noc_x, noc_y, address, size_bytes, use_4B_mode)

    def noc_read32(self, location: OnChipCoordinate, address: int, noc_id: int | None = None) -> int:
        result = self.noc_read(location, address, 4, noc_id, True)
        return int.from_bytes(result, byteorder="little")

    def noc_write(
        self,
        location: OnChipCoordinate,
        address: int,
        data: bytes,
        noc_id: int | None = None,
        use_4B_mode: bool | None = None,
    ):
        noc_x, noc_y = location._noc0_coord
        if noc_id is None:
            noc_id = 1 if self._context.use_noc1 else 0
        if use_4B_mode is None:
            use_4B_mode = self._context.use_4B_mode
        return self._umd_device.noc_write(noc_id, noc_x, noc_y, address, data, use_4B_mode)

    def noc_write32(self, location: OnChipCoordinate, address: int, data: int, noc_id: int | None = None):
        return self.noc_write(location, address, data.to_bytes(4, byteorder="little"), noc_id, True)

    def bar0_read32(self, address: int) -> int:
        return self._umd_device.bar0_read32(address)

    def bar0_write32(self, address: int, data: int):
        return self._umd_device.bar0_write32(address, data)

    def arc_msg(
        self,
        noc_id: int,
        msg_code: int,
        wait_for_done: bool,
        args: Sequence[int],
        timeout: datetime.timedelta | float,
    ):
        return self._umd_device.arc_msg(noc_id, msg_code, wait_for_done, args, timeout)

    def read_arc_telemetry_entry(self, noc_id: int | None, telemetry_tag: int) -> int:
        if noc_id is None:
            noc_id = 1 if self._context.use_noc1 else 0
        return self._umd_device.read_arc_telemetry_entry(noc_id, telemetry_tag)

    def get_remote_transfer_eth_core(self) -> tuple[int, int] | None:
        return self._umd_device.get_remote_transfer_eth_core()

    # Coordinate conversion functions (see coordinate.py for description of coordinate systems)
    def __noc_to_die(self, noc_loc, noc_id=0):
        noc_x, noc_y = noc_loc
        assert noc_id == 0
        return (self.NOC_0_X_TO_DIE_X[noc_x], self.NOC_0_Y_TO_DIE_Y[noc_y])

    def _init_coordinate_systems(self):
        # Fill in coordinates for each block type
        self._noc0_to_block_type: dict[tuple[int, int], str] = {}
        for block_type, locations in self._block_locations.items():
            for loc in locations:
                self._noc0_to_block_type[loc._noc0_coord] = block_type

        # Fill in coordinate maps from UMD coordinate manager
        self._from_noc0: dict[tuple[tuple[int, int], str], tuple[tuple[int, int], str]] = {}
        self._to_noc0: dict[tuple[tuple[int, int], str, str], tuple[int, int]] = {}
        umd_supported_coordinates = ["noc1", "logical", "translated"]
        unique_coordinates = ["noc1", "translated"]
        for noc0_location, block_type in self._noc0_to_block_type.items():
            core_type = self.block_types[block_type].core_type
            for coord_system in umd_supported_coordinates:
                try:
                    converted_location = self._umd_device.convert_from_noc0(
                        noc0_location[0], noc0_location[1], core_type, coord_system
                    )
                    self._from_noc0[(noc0_location, coord_system)] = (converted_location, core_type)
                    self._to_noc0[(converted_location, coord_system, core_type)] = noc0_location
                    if coord_system in unique_coordinates:
                        self._to_noc0[(converted_location, coord_system, "any")] = noc0_location
                except:
                    pass

            # Add coordinate systems that UMD does not support

            # Add die
            die_location = self.__noc_to_die(noc0_location)
            self._from_noc0[(noc0_location, "die")] = (die_location, core_type)
            self._to_noc0[(die_location, "die", core_type)] = noc0_location
            self._to_noc0[(die_location, "die", "any")] = noc0_location

    def to_noc0(self, coord_tuple: tuple[int, int], coord_system: str, core_type: str = "any") -> tuple[int, int]:
        try:
            return self._to_noc0[(coord_tuple, coord_system, core_type)]
        except:
            raise CoordinateTranslationError(
                f"to_noc0(coord_tuple={coord_tuple}, coord_system={coord_system}, core_type={core_type})"
            )

    def from_noc0(self, noc0_tuple: tuple[int, int], coord_system: str) -> tuple[tuple[int, int], str]:
        try:
            return self._from_noc0[(noc0_tuple, coord_system)]
        except:
            try:
                # Try to recover using UMD API
                converted_location = self._umd_device.convert_from_noc0(
                    noc0_tuple[0], noc0_tuple[1], "router_only", coord_system
                )
                return (converted_location, "router_only")
            except:
                raise CoordinateTranslationError(f"from_noc0(noc0_tuple={noc0_tuple}, coord_system={coord_system})")

    def is_translated_coordinate(self, x: int, y: int) -> bool:
        # Base class doesn't know if it is translated coordinate, but specialized classes do
        return False

    @abstractmethod
    @cache
    def get_block(self, location: OnChipCoordinate) -> NocBlock:
        """
        Returns the NOC block at the given location
        """
        pass

    @cache
    def get_blocks(self, block_type: str = "functional_workers") -> list[NocBlock]:
        """
        Returns all blocks of a given type
        """
        blocks: list[NocBlock] = []
        for location in self.get_block_locations(block_type):
            blocks.append(self.get_block(location))
        return blocks

    @cached_property
    def arc_block(self) -> ArcBlock:
        arc_blocks = self.get_blocks(block_type="arc")

        assert len(arc_blocks) == 1, "Expected a single ARC block"
        assert isinstance(arc_blocks[0], ArcBlock), "Expected a single ARC block"

        return arc_blocks[0]

    @cached_property
    def active_eth_block_locations(self) -> list[OnChipCoordinate]:
        active_channels: list[int] = []
        for src_chip, channels in self._context.cluster_descriptor.get_ethernet_connections().items():
            for src_chan, dest in channels.items():
                dest_chip, dest_chan = dest
                if dest_chip == self._id:
                    active_channels.append(dest_chan)
        return [self.get_block_locations(block_type="eth")[chan] for chan in active_channels]

    @cached_property
    def idle_eth_block_locations(self) -> list[OnChipCoordinate]:
        idle_block_locations = []
        for location in self.get_block_locations(block_type="eth"):
            if not location in self.active_eth_block_locations:
                idle_block_locations.append(location)

        return idle_block_locations

    @cached_property
    def active_eth_blocks(self) -> list[NocBlock]:
        return [self.get_block(location) for location in self.active_eth_block_locations]

    @cached_property
    def idle_eth_blocks(self) -> list[NocBlock]:
        return [self.get_block(location) for location in self.idle_eth_block_locations]

    @abstractmethod
    def get_tensix_registers_description(self) -> TensixRegisterDescription:
        pass

    @abstractmethod
    def get_tensix_debug_bus_description(self) -> TensixDebugBusDescription:
        pass

    def get_block_locations(self, block_type="functional_workers") -> list[OnChipCoordinate]:
        """
        Returns locations of all blocks of a given type
        """
        return self._block_locations[block_type]

    @cached_property
    def _block_locations(self) -> dict[str, list[OnChipCoordinate]]:
        """
        Returns locations of all blocks as dictionary of tuples (unchanged coordinates from YAML)
        """
        result: dict[str, list[OnChipCoordinate]] = {}
        for block_name, block_type in self.block_types.items():
            locs = []
            core_type = tt_umd.CoreType[block_type.core_type.upper()]
            if block_type.core_harvesting:
                core_coords = self._soc_descriptor.get_harvested_cores(core_type, tt_umd.CoordSystem.NOC0)
            else:
                core_coords = self._soc_descriptor.get_cores(core_type, tt_umd.CoordSystem.NOC0)

            for core_coord in core_coords:
                locs.append(OnChipCoordinate(core_coord.x, core_coord.y, "noc0", self, block_type.core_type))
            result[block_name] = locs
        return result

    @dataclass
    class BlockType:
        symbol: str
        desc: str
        core_type: str
        core_harvesting: bool
        color: str

    block_types = {
        "functional_workers": BlockType(
            symbol=".", desc="Functional worker", core_type="tensix", core_harvesting=False, color=util.CLR_GREEN
        ),
        "eth": BlockType(symbol="E", desc="Ethernet", core_type="eth", core_harvesting=False, color=util.CLR_YELLOW),
        "harvested_eth": BlockType(
            symbol="e", desc="Harvested Ethernet", core_type="eth", core_harvesting=True, color=util.CLR_RED
        ),
        "arc": BlockType(symbol="A", desc="ARC", core_type="arc", core_harvesting=False, color=util.CLR_GREY),
        "dram": BlockType(symbol="D", desc="DRAM", core_type="dram", core_harvesting=False, color=util.CLR_TEAL),
        "harvested_dram": BlockType(
            symbol="d", desc="Harvested DRAM", core_type="dram", core_harvesting=True, color=util.CLR_RED
        ),
        "pcie": BlockType(symbol="P", desc="PCIE", core_type="pcie", core_harvesting=False, color=util.CLR_GREY),
        "router_only": BlockType(
            symbol=" ", desc="Router only", core_type="router_only", core_harvesting=False, color=util.CLR_GREY
        ),
        "harvested_workers": BlockType(
            symbol="-", desc="Harvested", core_type="tensix", core_harvesting=True, color=util.CLR_RED
        ),
        "security": BlockType(
            symbol="S", desc="Security", core_type="security", core_harvesting=False, color=util.CLR_GREY
        ),
        "l2cpu": BlockType(symbol="C", desc="L2CPU", core_type="l2cpu", core_harvesting=False, color=util.CLR_GREY),
    }

    core_types = {v.core_type for v in block_types.values()}

    def get_block_type(self, loc: OnChipCoordinate) -> str:
        """
        Returns the type of block at the given location
        """
        return self._noc0_to_block_type[loc._noc0_coord]

    # Returns a string representation of the device. When printed, the string will
    # show the device blocks ascii graphically. It will emphasize blocks with locations given by emphasize_loc_list
    # See coordinate.py for valid values of axis_coordinates
    def render(self, axis_coordinate="die", cell_renderer=None, legend=None):
        rows: list[list[str]] = []

        # Retrieve all block locations
        all_block_locs = dict()
        hor_axis = OnChipCoordinate.horizontal_axis(axis_coordinate)
        ver_axis = OnChipCoordinate.vertical_axis(axis_coordinate)

        # Compute extents(range) of all coordinates in the UI
        ui_hor_range = (9999, -1)
        ui_ver_range = (9999, -1)
        for bt in self.block_types:
            b_locs = self.get_block_locations(block_type=bt)
            for loc in b_locs:
                try:
                    grid_loc = loc.to(axis_coordinate)
                    ui_hor = grid_loc[hor_axis]
                    ui_hor_range = (
                        min(ui_hor_range[0], ui_hor),
                        max(ui_hor_range[1], ui_hor),
                    )
                    ui_ver = grid_loc[ver_axis]
                    ui_ver_range = (
                        min(ui_ver_range[0], ui_ver),
                        max(ui_ver_range[1], ui_ver),
                    )
                    all_block_locs[(ui_hor, ui_ver)] = loc
                except:
                    pass

        screen_row_y = 0
        C = util.CLR_INFO
        E = util.CLR_END

        def append_horizontal_axis_labels(rows, ui_hor_range):
            row = [""] + [
                f"{C}%02d{E}" % i for i in range(ui_hor_range[0], ui_hor_range[1] + 1)
            ]  # This adds the X-axis labels
            rows.append(row)

        ver_range: Iterable[int]
        if OnChipCoordinate.vertical_axis_increasing_up(axis_coordinate):
            ver_range = reversed(range(ui_ver_range[0], ui_ver_range[1] + 1))
        else:
            ver_range = range(ui_ver_range[0], ui_ver_range[1] + 1)
            append_horizontal_axis_labels(rows, ui_hor_range)

        for ui_ver in ver_range:
            row = [f"{C}%02d{E}" % ui_ver]  # This adds the Y-axis label
            # 1. Add graphics
            for ui_hor in range(ui_hor_range[0], ui_hor_range[1] + 1):
                render_str = ""
                if (ui_hor, ui_ver) in all_block_locs:
                    if cell_renderer == None:
                        render_str = all_block_locs[(ui_hor, ui_ver)].to_str("logical")
                    else:
                        render_str = cell_renderer(all_block_locs[(ui_hor, ui_ver)])
                row.append(render_str)

            # 2. Add legend
            legend_y = screen_row_y
            if legend and legend_y < len(legend):
                row = row + [util.CLR_INFO + "    " + legend[legend_y] + util.CLR_END]

            rows.append(row)
            screen_row_y += 1

        if OnChipCoordinate.vertical_axis_increasing_up(axis_coordinate):
            append_horizontal_axis_labels(rows, ui_hor_range)

        table_str = tabulate(rows, tablefmt="plain", disable_numparse=True)
        return table_str

    # User friendly string representation of the device
    def __str__(self):
        return self.render()

    # Detailed string representation of the device
    def __repr__(self):
        return f"ID: {self.id()}, Arch: {self._arch}"


# end of class Device
