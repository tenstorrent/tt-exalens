# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod
from copy import deepcopy
from dataclasses import dataclass, replace
from functools import cached_property
from typing import Dict, Iterable, Iterator, List, Sequence, Tuple

from tabulate import tabulate
from ttexalens.context import Context
from ttexalens.debug_bus_signal_store import DebugBusSignalStore
from ttexalens.object import TTObject
from ttexalens import util as util
from ttexalens.coordinate import CoordinateTranslationError, OnChipCoordinate
from abc import abstractmethod

from ttexalens.util import DATA_TYPE
from ttexalens.debug_risc import get_risc_reset_shift, RiscDebug, RiscLoc
from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device


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


@dataclass
class TensixRegisterDescription:
    address: int = 0
    mask: int = 0xFFFFFFFF
    shift: int = 0
    data_type: DATA_TYPE = DATA_TYPE.INT_VALUE

    def clone(self, offset: int = 0):
        new_instance = deepcopy(self)
        new_instance.address += offset
        return new_instance

    def __str__(self):
        return f"{type(self).__name__}(address: {self.address:#x}, mask: {self.mask:#x}, shift: {self.shift}, native_data_type: {self.data_type})"


@dataclass
class DebugRegisterDescription(TensixRegisterDescription):
    pass


@dataclass
class ConfigurationRegisterDescription(TensixRegisterDescription):
    index: int = 0

    def __post_init__(self):
        self.address = self.address + self.index * 4

    def __str__(self):
        base_str = super().__str__()[:-1]
        return f"{base_str}, index: {self.index})"


@dataclass
class NocStatusRegisterDescription(TensixRegisterDescription):
    pass


@dataclass
class NocConfigurationRegisterDescription(TensixRegisterDescription):
    pass


@dataclass
class NocControlRegisterDescription(TensixRegisterDescription):
    pass


#
# Device class: generic API for talking to specific devices. This class is the parent of specific
# device classes (e.g. WormholeDevice, BlackholeDevice). The create class method is used to create
# a specific device.
#
class Device(TTObject):
    instructions: TensixInstructions = None
    DIE_X_TO_NOC_0_X: List[int] = []
    DIE_Y_TO_NOC_0_Y: List[int] = []
    DIE_X_TO_NOC_1_X: List[int] = []
    DIE_Y_TO_NOC_1_Y: List[int] = []
    NOC_0_X_TO_DIE_X: List[int] = []
    NOC_0_Y_TO_DIE_Y: List[int] = []
    NOC_1_X_TO_DIE_X: List[int] = []
    NOC_1_Y_TO_DIE_Y: List[int] = []
    PCI_ARC_RESET_BASE_ADDR: int = None
    NOC_ARC_RESET_BASE_ADDR: int = None
    PCI_ARC_CSM_DATA_BASE_ADDR: int = None
    NOC_ARC_CSM_DATA_BASE_ADDR: int = None
    PCI_ARC_ROM_DATA_BASE_ADDR: int = None
    NOC_ARC_ROM_DATA_BASE_ADDR: int = None
    NOC_REGISTER_OFFSET: int = None

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
            for risc_id in range(4):  # 4 because we have a hardware bug for debugging ncrisc
                risc_location = RiscLoc(coord, 0, risc_id)
                risc_debug = RiscDebug(risc_location, self._context)
                cores.append(risc_debug)

        # TODO: Can we debug eth cores?
        return cores

    # Class method to create a Device object given device architecture
    @staticmethod
    def create(arch, device_id, cluster_desc, device_desc_path: str, context: Context):
        dev = None
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
        self._has_jtag = (
            any(id in chip for chip in cluster_desc["chips_with_jtag"]) if "chips_with_jtag" in cluster_desc else False
        )

        self._init_coordinate_systems()
        self._init_arc_register_adresses()

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
        self._noc0_to_block_type: Dict[Tuple[int, int], str] = {}
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

    def get_block_locations(self, block_type="functional_workers") -> List[OnChipCoordinate]:
        """
        Returns locations of all blocks of a given type
        """
        return self._block_locations[block_type]

    def get_arc_block_location(self) -> OnChipCoordinate:
        """
        Returns OnChipCoordinate of the ARC block
        """
        arc_locations = self.get_block_locations(block_type="arc")

        assert len(arc_locations) == 1

        return arc_locations[0]

    @cached_property
    def _block_locations(self):
        """
        Returns locations of all blocks as dictionary of tuples (unchanged coordinates from YAML)
        """
        result: Dict[str, List[OnChipCoordinate]] = {}
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

    def get_block_type(self, loc: OnChipCoordinate) -> str:
        """
        Returns the type of block at the given location
        """
        return self._noc0_to_block_type.get(loc._noc0_coord)

    # Returns a string representation of the device. When printed, the string will
    # show the device blocks ascii graphically. It will emphasize blocks with locations given by emphasize_loc_list
    # See coordinate.py for valid values of axis_coordinates
    def render(self, axis_coordinate="die", cell_renderer=None, legend=None):
        dev = self.yaml_file.root
        rows: List[List[str]] = []

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
        return self._context.server_ifc.pci_read_tile(noc_id, self.id(), x, y, reg_addr, msg_size, data_format)

    def all_riscs_assert_soft_reset(self) -> None:
        """
        Put all risc cores under reset. Nothing will run until the reset is deasserted.
        """
        RISC_SOFT_RESET_0_ADDR = self.get_tensix_register_address("RISCV_DEBUG_REG_SOFT_RESET_0")

        ALL_SOFT_RESET = 0
        for risc_id in range(5):
            ALL_SOFT_RESET = ALL_SOFT_RESET | (1 << get_risc_reset_shift(risc_id))
        noc_id = 0

        for loc in self.get_block_locations(block_type="functional_workers"):
            write_words_to_device(loc, RISC_SOFT_RESET_0_ADDR, ALL_SOFT_RESET, self.id(), self._context)

            # Check what we wrote
            rst_reg = read_word_from_device(loc, RISC_SOFT_RESET_0_ADDR, self.id(), self._context)
            if rst_reg != ALL_SOFT_RESET:
                util.ERROR(f"Expected to write {ALL_SOFT_RESET:x} to {loc.to_str()} but read {rst_reg:x}")

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

    @abstractmethod
    def _get_tensix_register_map_keys(self) -> List[str]:
        pass

    @abstractmethod
    def _get_tensix_register_base_address(self, register_description: TensixRegisterDescription) -> int | None:
        pass

    @abstractmethod
    def _get_tensix_register_end_address(self, register_description: TensixRegisterDescription) -> int | None:
        pass

    @abstractmethod
    def _get_tensix_register_description(self, register_name: str) -> TensixRegisterDescription | None:
        pass

    @abstractmethod
    def _get_riscv_local_memory_base_address(self) -> int:
        pass

    @abstractmethod
    def _get_riscv_local_memory_size(self, risc_id: int) -> int:
        pass

    def get_tensix_register_description(self, register_name: str) -> TensixRegisterDescription:
        register_description = self._get_tensix_register_description(register_name)
        if register_description != None:
            base_address = self._get_tensix_register_base_address(register_description)
            if base_address != None:
                return register_description.clone(base_address)
            else:
                raise ValueError(f"Unknown tensix register base address for register: {register_name}")
        else:
            raise ValueError(f"Unknown tensix register name: {register_name}")

    def get_tensix_register_address(self, register_name: str) -> int:
        description = self.get_tensix_register_description(register_name)
        assert description.mask == 0xFFFFFFFF and description.shift == 0
        return description.address

    def get_riscv_run_status(self, loc: OnChipCoordinate) -> str:
        """
        Returns the riscv soft reset status as a string of 4 characters one for each riscv core.
        '-' means the core is in reset, 'R' means the core is running.
        """
        status_str = ""
        bt = self.get_block_type(loc)
        if bt == "functional_workers":
            for risc_id in range(4):
                risc_location = RiscLoc(loc, 0, risc_id)
                risc_debug = RiscDebug(risc_location, self._context)
                status_str += "-" if risc_debug.is_in_reset() else "R"
            return status_str
        if bt == "harvested_workers":
            return "----"
        return bt

    REGISTER_ADDRESSES: Dict[str, int] = {}

    def get_arc_register_addr(self, name: str) -> int:
        try:
            addr = self.REGISTER_ADDRESSES[name]
        except KeyError:
            raise ValueError(f"Unknown register name: {name}. Available registers: {self.REGISTER_ADDRESSES.keys()}")

        return addr

    def _init_arc_register_adresses(self):
        if len(self.get_block_locations("arc")) > 0:
            base_addr = self.PCI_ARC_RESET_BASE_ADDR if self._has_mmio else self.NOC_ARC_RESET_BASE_ADDR
            csm_data_base_addr = self.PCI_ARC_CSM_DATA_BASE_ADDR if self._has_mmio else self.NOC_ARC_CSM_DATA_BASE_ADDR
            rom_data_base_addr = self.PCI_ARC_ROM_DATA_BASE_ADDR if self._has_mmio else self.NOC_ARC_ROM_DATA_BASE_ADDR

            self.REGISTER_ADDRESSES = {
                "ARC_RESET_ARC_MISC_CNTL": base_addr + 0x100,
                "ARC_RESET_ARC_MISC_STATUS": base_addr + 0x104,
                "ARC_RESET_ARC_UDMIAXI_REGION": base_addr + 0x10C,
                "ARC_RESET_SCRATCH0": base_addr + 0x060,
                "ARC_RESET_SCRATCH1": base_addr + 0x064,
                "ARC_RESET_SCRATCH2": base_addr + 0x068,
                "ARC_RESET_SCRATCH3": base_addr + 0x06C,
                "ARC_RESET_SCRATCH4": base_addr + 0x070,
                "ARC_RESET_SCRATCH5": base_addr + 0x074,
                "ARC_CSM_DATA": csm_data_base_addr,
                "ARC_ROM_DATA": rom_data_base_addr,
            }

    @abstractmethod
    def get_debug_bus_signal_store(self, loc: OnChipCoordinate) -> DebugBusSignalStore:
        """
        Returns the debug bus signal store for the given location.
        """
        pass

    def _is_noc_register_description(self, description: TensixRegisterDescription) -> bool:
        return isinstance(
            description,
            (NocStatusRegisterDescription, NocConfigurationRegisterDescription, NocControlRegisterDescription),
        )

    def get_noc_register_address(self, reg_name: str, noc_id: int) -> int:
        """
        Get the address for a NOC register.

        Args:
            reg_name: Register name
            noc_id: NOC identifier (0 or 1)

        Returns:
            Register address

        Raises:
            ValueError: If reg_name is not a NOC register or noc_id is invalid
        """
        if noc_id not in (0, 1):
            raise ValueError(f"Invalid NOC identifier: {noc_id}. Must be 0 or 1.")

        description = self.get_tensix_register_description(reg_name)

        # Validate this is a NOC register
        if not self._is_noc_register_description(description):
            raise ValueError(f"Register {reg_name} is not a NOC register")

        base_addr = description.address
        return base_addr + (noc_id * self.NOC_REGISTER_OFFSET)

    def get_noc_register_names(self) -> List[str]:
        """
        Get the list of NOC register names.

        Returns:
            List of NOC register descriptions
        """
        return [
            name
            for name in self._get_tensix_register_map_keys()
            if self._is_noc_register_description(self.get_tensix_register_description(name))
        ]


# end of class Device
