# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from functools import cached_property
import os, struct, ast
from typing import List, Sequence
from socket import timeout
from tabulate import tabulate
from ttlens.tt_lens_context import Context
from ttlens.tt_object import TTObject
from ttlens import tt_util as util
from ttlens.tt_coordinate import OnChipCoordinate, CoordinateTranslationError
from collections import namedtuple
from abc import ABC, abstractmethod
from typing import Dict
from ttlens.tt_debug_risc import get_risc_reset_shift, RiscDebug, RiscLoc
from ttlens.tt_lens_lib import read_word_from_device, write_words_to_device


class TensixInstructions(ABC):
    def __init__(self):
        pass


TensixRegisterDescription = namedtuple("TensixRegisterDescription", ["address", "mask", "shift"])

#
# Device class: generic API for talking to specific devices. This class is the parent of specific
# device classes (e.g. GrayskullDevice, WormholeDevice). The create class method is used to create
# a specific device.
#
class Device(TTObject):
    # NOC reg type
    class RegType:
        Cmd = 0
        Config = 1
        Status = 2

    # Class variable denoting the number of devices created
    num_devices = 0

    # See tt_coordinate.py for description of coordinate systems
    tensix_row_to_netlist_row = dict()
    netlist_row_to_tensix_row = dict()

    # Maps to store translation table from nocVirt to nocTr and vice versa
    nocVirt_to_nocTr_map = dict()
    nocTr_to_nocVirt_map = dict()

    # Maps to store translation table from noc0 to nocTr and vice versa
    nocTr_y_to_noc0_y = dict()
    noc0_y_to_nocTr_y = dict()

    instructions = TensixInstructions()

    @cached_property
    def debuggable_cores(self):
        # Base implementation for grayskull, wormhole and blackhole
        cores: List[RiscDebug] = []
        for coord in self.get_block_locations("functional_workers"):
            for risc_id in range(4):  # 4 because we have a hardware bug for debugging ncrisc
                risc_location = RiscLoc(coord, 0, risc_id)
                risc_debug = RiscDebug(risc_location, self._context)
                cores.append(risc_debug)

        # TODO: Can we debug eth cores?
        return cores

    # Class method to create a Device object given device architecture
    def create(arch, device_id, cluster_desc, device_desc_path: str, context: Context):
        dev = None
        if arch.lower() == "grayskull":
            from ttlens import tt_grayskull

            dev = tt_grayskull.GrayskullDevice(
                id=device_id, arch=arch, cluster_desc=cluster_desc, device_desc_path=device_desc_path, context=context
            )
        if "wormhole" in arch.lower():
            from ttlens import tt_wormhole

            dev = tt_wormhole.WormholeDevice(
                id=device_id, arch=arch, cluster_desc=cluster_desc, device_desc_path=device_desc_path, context=context
            )
        if "blackhole" in arch.lower():
            from ttlens import tt_blackhole

            dev = tt_blackhole.BlackholeDevice(
                id=device_id, arch=arch, cluster_desc=cluster_desc, device_desc_path=device_desc_path, context=context
            )

        if dev is None:
            raise RuntimeError(f"Architecture {arch} is not supported")

        return dev

    @abstractmethod
    def get_harvested_noc0_y_rows(self):
        pass

    def _create_tensix_netlist_harvesting_map(self):
        tensix_row = 0
        netlist_row = 0
        self.tensix_row_to_netlist_row = dict()  # Clear any existing map
        self.netlist_row_to_tensix_row = dict()
        harvested_noc0_y_rows = self.get_harvested_noc0_y_rows()

        for noc0_y in range(0, self.row_count()):
            if noc0_y == 0 or noc0_y == 6:
                pass  # Skip Ethernet rows
            else:
                if noc0_y in harvested_noc0_y_rows:
                    pass  # Skip harvested rows
                else:
                    self.netlist_row_to_tensix_row[netlist_row] = tensix_row
                    self.tensix_row_to_netlist_row[tensix_row] = netlist_row
                    netlist_row += 1
                tensix_row += 1

    def _create_nocTr_noc0_harvesting_map(self):
        bitmask = self._harvesting["harvest_mask"] if self._harvesting else 0

        self.nocTr_y_to_noc0_y = dict()  # Clear any existing map
        self.noc0_y_to_nocTr_y = dict()
        for nocTr_y in range(0, self.row_count()):
            self.nocTr_y_to_noc0_y[nocTr_y] = nocTr_y  # Identity mapping for rows < 16

        num_harvested_rows = bin(bitmask).count("1")
        self._handle_harvesting_for_nocTr_noc0_map(num_harvested_rows)

        # 4. Create reverse map
        for nocTr_y in self.nocTr_y_to_noc0_y:
            self.noc0_y_to_nocTr_y[self.nocTr_y_to_noc0_y[nocTr_y]] = nocTr_y

        # 4. Print
        # for tr_row in reversed (range (16, 16 + self.row_count())):
        #     print(f"nocTr row {tr_row} => noc0 row {self.nocTr_y_to_noc0_y[tr_row]}")

        # print (f"Created nocTr to noc0 harvesting map for bitmask: {bitmask}")

    def _create_harvesting_maps(self):
        self._create_tensix_netlist_harvesting_map()
        self._create_nocTr_noc0_harvesting_map()

    def _create_nocVirt_to_nocTr_map(self):
        harvested_coord_translation_str = self._context.server_ifc.get_harvester_coordinate_translation(self._id)
        self.nocVirt_to_nocTr_map = ast.literal_eval(harvested_coord_translation_str)  # Eval string to dict
        self.nocTr_to_nocVirt_map = {v: k for k, v in self.nocVirt_to_nocTr_map.items()}  # Create inverse map as well

    def tensix_to_netlist(self, tensix_loc):
        return (self.tensix_row_to_netlist_row[tensix_loc[0]], tensix_loc[1])

    def netlist_to_tensix(self, netlist_loc):
        return (self.netlist_row_to_tensix_row[netlist_loc[0]], netlist_loc[1])

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
        elif arch.lower() == "grayskull":
            self._harvesting = None
        else:
            raise util.TTFatalException(f"Cluster description is not valid. 'harvesting_desc' reads: {harvesting_desc}")

        self._create_harvesting_maps()
        self._create_nocVirt_to_nocTr_map()
        util.DEBUG(
            "Opened device: id=%d, arch=%s, has_mmio=%s, harvesting=%s" % (id, arch, self._has_mmio, self._harvesting)
        )

        self.block_locations_cache = dict()
        self._init_register_addresses()

    # Coordinate conversion functions (see tt_coordinate.py for description of coordinate systems)
    def die_to_noc(self, phys_loc, noc_id=0):
        die_x, die_y = phys_loc
        if noc_id == 0:
            return (self.DIE_X_TO_NOC_0_X[die_x], self.DIE_Y_TO_NOC_0_Y[die_y])
        else:
            return (self.DIE_X_TO_NOC_1_X[die_x], self.DIE_Y_TO_NOC_1_Y[die_y])

    def noc_to_die(self, noc_loc, noc_id=0):
        noc_x, noc_y = noc_loc
        if noc_id == 0:
            return (self.NOC_0_X_TO_DIE_X[noc_x], self.NOC_0_Y_TO_DIE_Y[noc_y])
        else:
            return (self.NOC_1_X_TO_DIE_X[noc_x], self.NOC_1_Y_TO_DIE_Y[noc_y])

    def noc0_to_noc1(self, noc0_loc):
        phys_loc = self.noc_to_die(noc0_loc, noc_id=0)
        return self.die_to_noc(phys_loc, noc_id=1)

    def noc1_to_noc0(self, noc1_loc):
        phys_loc = self.noc_to_die(noc1_loc, noc_id=1)
        return self.die_to_noc(phys_loc, noc_id=0)

    def nocVirt_to_nocTr(self, noc0_loc):
        return self.nocVirt_to_nocTr_map[noc0_loc]

    def nocTr_to_nocVirt(self, nocTr_loc):
        return self.nocTr_to_nocVirt_map[nocTr_loc]

    def nocTr_to_noc0(self, nocTr_loc):
        noc0_y = self.nocTr_y_to_noc0_y[nocTr_loc[1]]
        noc0_x = self.NOCTR_X_TO_NOC0_X[nocTr_loc[0]] if nocTr_loc[0] >= 16 else nocTr_loc[0]
        return (noc0_x, noc0_y)

    def noc0_to_nocTr(self, noc0_loc):
        nocTr_y = self.noc0_y_to_nocTr_y[noc0_loc[1]]
        nocTr_x = self.NOC0_X_TO_NOCTR_X[noc0_loc[0]]
        return (nocTr_x, nocTr_y)

    def nocVirt_to_noc0(self, nocVirt_loc):
        nocTr_loc = self.nocVirt_to_nocTr(nocVirt_loc)
        return self.nocTr_to_noc0(nocTr_loc)

    def noc0_to_nocVirt(self, noc0_loc):
        nocTr_loc = self.noc0_to_nocTr(noc0_loc)
        try:
            nocVirt = self.nocTr_to_nocVirt(nocTr_loc)
        except KeyError:
            # DRAM locations are not in nocTr_to_nocVirt map. Use noc0 coordinates directly.
            nocVirt = noc0_loc
        return nocVirt

    def noc0_to_netlist(self, noc0_loc):
        try:
            c = self.tensix_to_netlist(self.noc0_to_tensix(noc0_loc))
            return (c[0], c[1])
        except KeyError:
            raise CoordinateTranslationError(
                f"noc0_to_netlist: noc0_loc {noc0_loc} does not translate to a valid netlist location"
            )

    def netlist_to_noc0(self, netlist_loc):
        try:
            c = self.tensix_to_noc0(self.netlist_to_tensix(netlist_loc))
            return (c[0], c[1])
        except KeyError:
            raise CoordinateTranslationError(
                f"netlist_to_noc0: netlist_loc {netlist_loc} does not translate to a valid noc0 location"
            )

    def get_block_locations(self, block_type="functional_workers"):
        """
        Returns locations of all blocks of a given type
        """
        locs = []
        dev = self.yaml_file.root

        for loc_or_list in dev[block_type]:
            if type(loc_or_list) != str and isinstance(loc_or_list, Sequence):
                for loc in loc_or_list:
                    locs.append(OnChipCoordinate.create(loc, self, "nocVirt"))
            else:
                locs.append(OnChipCoordinate.create(loc_or_list, self, "nocVirt"))
        return locs

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
        result = {}
        for block_type in self.block_types:
            locs = []
            dev = self.yaml_file.root

            for loc_or_list in dev[block_type]:
                if type(loc_or_list) != str and isinstance(loc_or_list, Sequence):
                    for loc in loc_or_list:
                        locs.append(OnChipCoordinate.create(loc, self, "noc0")._noc0_coord)
                else:
                    locs.append(OnChipCoordinate.create(loc_or_list, self, "noc0")._noc0_coord)
            result[block_type] = locs
        return result

    block_types = {
        "functional_workers": {"symbol": ".", "desc": "Functional worker"},
        "eth": {"symbol": "E", "desc": "Ethernet"},
        "arc": {"symbol": "A", "desc": "ARC"},
        "dram": {"symbol": "D", "desc": "DRAM"},
        "pcie": {"symbol": "P", "desc": "PCIE"},
        "router_only": {"symbol": " ", "desc": "Router only"},
        "harvested_workers": {"symbol": "-", "desc": "Harvested"},
    }

    def get_block_type(self, loc):
        """
        Returns the type of block at the given location
        """
        dev = self.yaml_file.root
        for block_type in self.block_types:
            block_locations = self.get_block_locations(block_type=block_type)
            if loc in block_locations:
                return block_type
        return None

    # Returns a string representation of the device. When printed, the string will
    # show the device blocks ascii graphically. It will emphasize blocks with locations given by emphasize_loc_list
    # See tt_coordinates for valid values of axis_coordinates
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
                        render_str = all_block_locs[(ui_hor, ui_ver)].to_str("netlist")
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

    @abstractmethod
    def get_tensix_configuration_register_base(self) -> int:
        pass

    @abstractmethod
    def get_tenxis_debug_register_base(self) -> int:
        pass

    @abstractmethod
    def get_configuration_register_description(self, register_name: str) -> TensixRegisterDescription:
        pass

    @abstractmethod
    def get_debug_register_description(self, register_name: str) -> TensixRegisterDescription:
        pass

    def get_tensix_register_description(self, register_name: str) -> TensixRegisterDescription:
        register_description = self.get_configuration_register_description(register_name)
        if register_description != None:
            base_register_address = self.get_tensix_configuration_register_base()
        else:
            register_description = self.get_debug_register_description(register_name)
            if register_description != None:
                base_register_address = self.get_tenxis_debug_register_base()
            else:
                raise ValueError(f"Unknown tensix register name: {register_name}")
        return register_description._replace(address=base_register_address + register_description.address)

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
        return bt

    REGISTER_ADDRESSES = {}

    def get_register_addr(self, name: str) -> int:
        try:
            addr = self.REGISTER_ADDRESSES[name]
        except KeyError:
            raise ValueError(f"Unknown register name: {name}. Available registers: {self.REGISTER_ADDRESSES.keys()}")

        return addr

    def _init_register_addresses(self):
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


# end of class Device

# This is based on runtime_utils.cpp:get_soc_desc_path()
def get_soc_desc_path(chip, output_dir):
    if os.path.exists(os.path.join(output_dir, "device_desc_runtime", f"{chip}.yaml")):
        file_to_use = os.path.join(output_dir, "device_desc_runtime", f"{chip}.yaml")
    elif os.path.exists(os.path.join(output_dir, "device_descs")):
        file_to_use = os.path.join(output_dir, "device_descs", f"{chip}.yaml")
    else:
        file_to_use = os.path.join(output_dir, "device_desc.yaml")
    return file_to_use
