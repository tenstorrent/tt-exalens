# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from functools import cache, cached_property
from typing import Iterable, Sequence

from tabulate import tabulate
from ttexalens.context import Context
from ttexalens.hardware.arc_block import ArcBlock
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.risc_debug import RiscDebug
from ttexalens.hardware.tensix_configuration_registers_description import TensixConfigurationRegistersDescription
from ttexalens.object import TTObject
from ttexalens import util as util
from ttexalens.coordinate import CoordinateTranslationError, OnChipCoordinate
from abc import abstractmethod


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
    def create(arch, device_id, cluster_desc, device_desc_path: str, context: Context):
        if "wormhole" in arch.lower():
            from ttexalens.hw.tensix.wormhole import wormhole

            return wormhole.WormholeDevice(
                id=device_id, arch=arch, cluster_desc=cluster_desc, device_desc_path=device_desc_path, context=context
            )
        if "blackhole" in arch.lower():
            from ttexalens.hw.tensix.blackhole import blackhole

            return blackhole.BlackholeDevice(
                id=device_id, arch=arch, cluster_desc=cluster_desc, device_desc_path=device_desc_path, context=context
            )

        if "quasar" in arch.lower():
            from ttexalens.hw.tensix.quasar import quasar

            return quasar.QuasarDevice(
                id=device_id, arch=arch, cluster_desc=cluster_desc, device_desc_path=device_desc_path, context=context
            )

        raise RuntimeError(f"Architecture {arch} is not supported")

    @cached_property
    def yaml_file(self):
        return util.YamlFile(self._context.server_ifc, self._device_desc_path)

    def __init__(self, id: int, arch: str, cluster_desc, device_desc_path: str, context: Context):
        self._id: int = id
        self._arch = arch
        self._device_desc_path = device_desc_path
        self._context = context
        self._has_mmio = any(id in chip for chip in cluster_desc["chips_with_mmio"])
        self._has_jtag = cluster_desc["io_device_type"] == "JTAG"
        self.cluster_desc = cluster_desc
        self._init_coordinate_systems()
        self.unique_id = self._context.server_ifc.get_device_unique_id(self._id)

    @cached_property
    def _firmware_version(self):
        return util.FirmwareVersion(self._context.server_ifc.get_firmware_version(self._id))

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
        self._from_noc0 = {}
        self._to_noc0 = {}
        umd_supported_coordinates = ["noc1", "logical", "translated"]
        unique_coordinates = ["noc1", "translated"]
        for noc0_location, block_type in self._noc0_to_block_type.items():
            core_type = self.block_types[block_type]["core_type"]
            for coord_system in umd_supported_coordinates:
                try:
                    converted_location = self._context.server_ifc.convert_from_noc0(
                        self._id, noc0_location[0], noc0_location[1], core_type, coord_system
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
                converted_location = self._context.server_ifc.convert_from_noc0(
                    self._id, noc0_tuple[0], noc0_tuple[1], "router_only", coord_system
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
    def get_blocks(self, block_type="functional_workers"):
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
        active_channels = []
        for connection in self.cluster_desc["ethernet_connections"]:
            for endpoint in connection:
                if endpoint["chip"] == self._id:
                    active_channels.append(endpoint["chan"])

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
    def get_tensix_configuration_registers_description(self) -> TensixConfigurationRegistersDescription:
        pass

    def get_block_locations(self, block_type="functional_workers") -> list[OnChipCoordinate]:
        """
        Returns locations of all blocks of a given type
        """
        return self._block_locations[block_type]

    @cached_property
    def _block_locations(self):
        """
        Returns locations of all blocks as dictionary of tuples (unchanged coordinates from YAML)
        """
        result: dict[str, list[OnChipCoordinate]] = {}
        for block_type in self.block_types:
            locs = []
            dev = self.yaml_file.root

            for loc_or_list in dev[block_type]:
                if type(loc_or_list) != str and isinstance(loc_or_list, Sequence):
                    for loc in loc_or_list:
                        locs.append(OnChipCoordinate.create(loc, self, "noc0"))
                else:
                    locs.append(OnChipCoordinate.create(loc_or_list, self, "noc0"))
            result[block_type] = locs
        return result

    block_types = {
        "functional_workers": {
            "symbol": ".",
            "desc": "Functional worker",
            "core_type": "tensix",
            "color": util.CLR_GREEN,
        },
        "eth": {"symbol": "E", "desc": "Ethernet", "core_type": "eth", "color": util.CLR_YELLOW},
        "arc": {"symbol": "A", "desc": "ARC", "core_type": "arc", "color": util.CLR_GREY},
        "dram": {"symbol": "D", "desc": "DRAM", "core_type": "dram", "color": util.CLR_TEAL},
        "pcie": {"symbol": "P", "desc": "PCIE", "core_type": "pcie", "color": util.CLR_GREY},
        "router_only": {"symbol": " ", "desc": "Router only", "core_type": "router_only", "color": util.CLR_GREY},
        "harvested_workers": {"symbol": "-", "desc": "Harvested", "core_type": "tensix", "color": util.CLR_RED},
        "security": {"symbol": "S", "desc": "Security", "core_type": "security", "color": util.CLR_GREY},
        "l2cpu": {"symbol": "C", "desc": "L2CPU", "core_type": "l2cpu", "color": util.CLR_GREY},
    }

    core_types = {v["core_type"] for v in block_types.values()}

    def get_block_type(self, loc: OnChipCoordinate) -> str:
        """
        Returns the type of block at the given location
        """
        return self._noc0_to_block_type[loc._noc0_coord]

    # Returns a string representation of the device. When printed, the string will
    # show the device blocks ascii graphically. It will emphasize blocks with locations given by emphasize_loc_list
    # See coordinate.py for valid values of axis_coordinates
    def render(self, axis_coordinate="die", cell_renderer=None, legend=None):
        dev = self.yaml_file.root
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

    def pci_read_tile(self, x, y, z, reg_addr, msg_size, data_format):
        noc_id = 1 if self._context.use_noc1 else 0
        return self._context.server_ifc.pci_read_tile(noc_id, self._id, x, y, reg_addr, msg_size, data_format)


# end of class Device
