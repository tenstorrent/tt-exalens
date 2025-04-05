# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from dataclasses import dataclass, replace
from functools import cached_property
from typing import List, Sequence, Tuple, Union

from tabulate import tabulate
from ttexalens.context import Context
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.object import TTObject
from ttexalens import util as util
from ttexalens.coordinate import CoordinateTranslationError, OnChipCoordinate
from abc import abstractmethod

from ttexalens.risc_debug import RiscDebug, RiscLocation
from ttexalens.register_store import RegisterStore
from ttexalens.risc_info import RiscInfo
from ttexalens.tensix_debug import TensixDebug
from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device


class TensixInstructions:
    def __init__(self, ops: __module__):
        for func_name in dir(ops):
            func = getattr(ops, func_name)
            if callable(func):
                static_method = staticmethod(func)
                setattr(self.__class__, func_name, static_method)


#
# Device class: generic API for talking to specific devices. This class is the parent of specific
# device classes (e.g. WormholeDevice, BlackholeDevice). The create class method is used to create
# a specific device.
#
class Device(TTObject):
    # NOC reg type
    class RegType:
        Cmd = 0
        Config = 1
        Status = 2

    @cached_property
    def debuggable_cores(self):
        # Base implementation for wormhole and blackhole
        cores: List[RiscDebug] = []
        for coord in self.get_block_locations("functional_workers"):
            for risc_name in self.get_risc_names_for_location(coord):
                risc_debug = self.get_risc_debug(coord, risc_name)
                cores.append(risc_debug)

        # TODO: Can we debug eth cores?
        return cores

    # Class method to create a Device object given device architecture
    def create(arch, device_id, cluster_desc, device_desc_path: str, context: Context):
        dev = None
        if "wormhole" in arch.lower():
            from ttexalens.hw.tensix.wormhole import wormhole

            dev = wormhole.WormholeDevice(
                id=device_id, arch=arch, cluster_desc=cluster_desc, device_desc_path=device_desc_path, context=context
            )
        if "blackhole" in arch.lower():
            from ttexalens.hw.tensix.blackhole import blackhole

            dev = blackhole.BlackholeDevice(
                id=device_id, arch=arch, cluster_desc=cluster_desc, device_desc_path=device_desc_path, context=context
            )

        if "quasar" in arch.lower():
            from ttexalens.hw.tensix.quasar import quasar

            dev = quasar.QuasarDevice(
                id=device_id, arch=arch, cluster_desc=cluster_desc, device_desc_path=device_desc_path, context=context
            )

        if dev is None:
            raise RuntimeError(f"Architecture {arch} is not supported")

        return dev

    @cached_property
    def yaml_file(self):
        return util.YamlFile(self._context.server_ifc, self._device_desc_path)

    def __init__(self, id, arch, cluster_desc, device_desc_path: str, context: Context):
        self._id = id
        self._arch = arch
        self._has_mmio = False
        self._has_jtag = False
        self._device_desc_path = device_desc_path
        self._context = context
        for chip in cluster_desc["chips_with_mmio"]:
            if id in chip:
                self._has_mmio = True
                break
        if "chips_with_jtag" in cluster_desc:
            for chip in cluster_desc["chips_with_jtag"]:
                if id in chip:
                    self._has_jtag = True
                    break

        # Check if harvesting_desc is an array and has id+1 entries at the least
        harvesting_desc = cluster_desc["harvesting"]
        if isinstance(harvesting_desc, Sequence) and len(harvesting_desc) > id:
            device_desc = harvesting_desc[id]
            if id not in device_desc:
                raise util.TTFatalException(f"Key {id} not found in: {device_desc}")
            self._harvesting = device_desc[id]
        elif isinstance(harvesting_desc, dict) or isinstance(harvesting_desc, util.RymlLazyDictionary):
            if id not in harvesting_desc:
                raise util.TTFatalException(f"Key {id} not found in: {harvesting_desc}")
            self._harvesting = harvesting_desc[id]
        else:
            raise util.TTFatalException(f"Cluster description is not valid. 'harvesting_desc' reads: {harvesting_desc}")
        util.DEBUG(
            "Opened device: id=%d, arch=%s, has_mmio=%s, harvesting=%s" % (id, arch, self._has_mmio, self._harvesting)
        )

        self._init_coordinate_systems()

    # Coordinate conversion functions (see coordinate.py for description of coordinate systems)
    def __die_to_noc(self, die_loc, noc_id=0):
        die_x, die_y = die_loc
        if noc_id == 0:
            return (self.DIE_X_TO_NOC_0_X[die_x], self.DIE_Y_TO_NOC_0_Y[die_y])
        else:
            return (self.DIE_X_TO_NOC_1_X[die_x], self.DIE_Y_TO_NOC_1_Y[die_y])

    def __noc_to_die(self, noc_loc, noc_id=0):
        noc_x, noc_y = noc_loc
        if noc_id == 0:
            return (self.NOC_0_X_TO_DIE_X[noc_x], self.NOC_0_Y_TO_DIE_Y[noc_y])
        else:
            return (self.NOC_1_X_TO_DIE_X[noc_x], self.NOC_1_Y_TO_DIE_Y[noc_y])

    def __noc0_to_noc1(self, noc0_loc):
        phys_loc = self.__noc_to_die(noc0_loc, noc_id=0)
        return self.__die_to_noc(phys_loc, noc_id=1)

    def _init_coordinate_systems(self):
        # Fill in coordinates for each block type
        self._noc0_to_block_type = {}
        for block_type, locations in self._block_locations.items():
            for loc in locations:
                self._noc0_to_block_type[loc._noc0_coord] = block_type

        # Fill in coordinate maps from UMD coordinate manager
        self._from_noc0 = {}
        self._to_noc0 = {}
        umd_supported_coordinates = ["logical", "virtual", "translated"]
        unique_coordinates = ["virtual", "translated"]
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

            # Add noc1
            noc1_location = self.__noc0_to_noc1(noc0_location)
            self._from_noc0[(noc0_location, "noc1")] = (noc1_location, core_type)
            self._to_noc0[(noc1_location, "noc1", core_type)] = noc0_location
            self._to_noc0[(noc1_location, "noc1", "any")] = noc0_location

            # Add die
            die_location = self.__noc_to_die(noc0_location)
            self._from_noc0[(noc0_location, "die")] = (die_location, core_type)
            self._to_noc0[(die_location, "die", core_type)] = noc0_location
            self._to_noc0[(die_location, "die", "any")] = noc0_location

    def to_noc0(self, coord_tuple: Tuple[int, int], coord_system: str, core_type: str = "any") -> Tuple[int, int]:
        try:
            return self._to_noc0[(coord_tuple, coord_system, core_type)]
        except:
            raise CoordinateTranslationError(
                f"to_noc0(coord_tuple={coord_tuple}, coord_system={coord_system}, core_type={core_type})"
            )

    def from_noc0(self, noc0_tuple: Tuple[int, int], coord_system: str) -> Tuple[Tuple[int, int], str]:
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

    def get_block_locations(self, block_type="functional_workers"):
        """
        Returns locations of all blocks of a given type
        """
        return self._block_locations[block_type]

    def get_arc_block_location(self) -> OnChipCoordinate:
        """
        Returns OnChipCoordinate of the ARC block
        """
        arc_locations = self.get_block_locations(block_type="arc")
        if len(arc_locations) == 0:
            raise ValueError("No ARC block found")
        assert len(arc_locations) == 1
        return arc_locations[0]

    @cached_property
    def _block_locations(self):
        """
        Returns locations of all blocks as dictionary of tuples (unchanged coordinates from YAML)
        """
        result = {}
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
    }

    core_types = {v["core_type"] for v in block_types.values()}

    def get_block_type(self, loc: OnChipCoordinate):
        """
        Returns the type of block at the given location
        """
        return self._noc0_to_block_type.get(loc._noc0_coord)

    # Returns a string representation of the device. When printed, the string will
    # show the device blocks ascii graphically. It will emphasize blocks with locations given by emphasize_loc_list
    # See coordinate.py for valid values of axis_coordinates
    def render(self, axis_coordinate="die", cell_renderer=None, legend=None):
        dev = self.yaml_file.root
        rows = []

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
        return self._context.server_ifc.pci_read_tile(self.id(), x, y, reg_addr, msg_size, data_format)

    # ALU GETTER
    def get_alu_config(self) -> List[dict]:
        return []

    # UNPACKER GETTERS

    def get_unpack_tile_descriptor(self) -> List[dict]:
        return []

    def get_unpack_config(self) -> List[dict]:
        return []

    # PACKER GETTERS

    def get_pack_config(self) -> List[dict]:
        return []

    def get_relu_config(self) -> List[dict]:
        return []

    def get_pack_dest_rd_ctrl(self) -> List[dict]:
        return []

    def get_pack_edge_offset(self) -> List[dict]:
        return []

    def get_pack_counters(self) -> List[dict]:
        return []

    # TODO: Replace arc registers with get_arc_register_store. This requires Arc refactor!!!!
    def get_arc_register_addr(self, name: str) -> int:
        try:
            register_store = self.get_arc_register_store()
            if self._has_mmio:
                return register_store.get_register_internal_address(name)
            else:
                return register_store.get_register_noc_address(name)
        except KeyError:
            raise ValueError(f"Unknown register name: {name}. Available registers: {self.REGISTER_ADDRESSES.keys()}")

    def get_debug_bus_signal_store(
        self, location: OnChipCoordinate, neo_id: Union[int, None] = None
    ) -> DebugBusSignalStore:
        """
        Returns the debug bus signal store for the given coordinate.
        """
        block_type = self.get_block_type(location)
        debug_bus_signal_store = self._get_debug_bus_signal_store_for_block(block_type, location, neo_id)
        if debug_bus_signal_store is None:
            raise ValueError(f"Unknown debug bus signal store for block type {block_type} at location {location}")
        return debug_bus_signal_store

    @abstractmethod
    def _get_debug_bus_signal_store_for_block(
        self, block_type: str, location: OnChipCoordinate, neo_id: Union[int, None] = None
    ) -> Union[DebugBusSignalStore, None]:
        """
        Returns the debug bus signal store for the given block type and coordinate.
        """
        pass

    def get_register_store(
        self, location: OnChipCoordinate, noc_id: Union[int, None] = None, neo_id: Union[int, None] = None
    ) -> RegisterStore:
        """
        Returns the register store for the given coordinate.
        """
        block_type = self.get_block_type(location)
        register_store = self._get_register_store_for_block(block_type, location, noc_id, neo_id)
        if register_store is None:
            raise ValueError(f"Unknown register store for block type {block_type} at location {location}")
        return register_store

    @abstractmethod
    def _get_register_store_for_block(
        self,
        block_type: str,
        location: OnChipCoordinate,
        noc_id: Union[int, None] = None,
        neo_id: Union[int, None] = None,
    ) -> Union[RegisterStore, None]:
        """
        Returns the register store for the given block type and coordinate.
        """
        pass

    def get_arc_register_store(self) -> RegisterStore:
        """
        Returns the register store for the ARC block.
        """
        return self.get_register_store(self.get_arc_block_location())

    def get_risc_names_for_location(self, location: OnChipCoordinate, neo_id: Union[int, None] = None) -> List[str]:
        """
        Returns the names of the RISC cores available for the given location.
        """
        block_type = self.get_block_type(location)
        return self._get_risc_names_for_location(block_type, location, neo_id)

    @abstractmethod
    def _get_risc_names_for_location(
        self, block_type: str, location: OnChipCoordinate, neo_id: Union[int, None] = None
    ) -> List[str]:
        """
        Returns the names of the RISC cores available for the given location.
        """
        pass

    @abstractmethod
    def get_risc_info(self, location: OnChipCoordinate, risc_name: str, neo_id: Union[int, None] = None) -> RiscInfo:
        """
        Returns the RISC info object for the given location and RISC name.
        """
        pass

    @abstractmethod
    def get_risc_debug(
        self,
        location: OnChipCoordinate,
        risc_name: str,
        noc_id: Union[int, None] = None,
        neo_id: Union[int, None] = None,
        verbose: bool = False,
    ) -> RiscDebug:
        """
        Returns the RISC debug object for the given location and RISC name.
        """
        pass

    @abstractmethod
    def get_tensix_debug(
        self, location: OnChipCoordinate, neo_id: Union[int, None] = None, verbose: bool = False
    ) -> TensixDebug:
        """
        Returns the Tensix debug object for the given location and RISC name.
        """
        pass


# end of class Device
