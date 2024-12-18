# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_util as util
from ttlens import tt_device
from ttlens.tt_coordinate import CoordinateTranslationError, OnChipCoordinate
from ttlens.tt_lens_lib import read_word_from_device


class WormholeInstructions(tt_device.TensixInstructions):
    def __init__(self):
        super().__init__()
        import ttlens.tt_wormhole_ops as ops

        for func_name in dir(ops):
            func = getattr(ops, func_name)
            if callable(func):
                static_method = staticmethod(func)
                setattr(self.__class__, func_name, static_method)


#
# Device
#
class WormholeDevice(tt_device.Device):
    SIG_SEL_CONST = 5
    # IMPROVE: some of this can be read from architecture yaml file
    DRAM_CHANNEL_TO_NOC0_LOC = [(0, 11), (0, 5), (5, 11), (5, 2), (5, 8), (5, 5)]

    # Physical location mapping. Physical coordinates are the geografical coordinates on a chip's die.
    DIE_X_TO_NOC_0_X = [0, 9, 1, 8, 2, 7, 3, 6, 4, 5]
    DIE_Y_TO_NOC_0_Y = [0, 11, 1, 10, 2, 9, 3, 8, 4, 7, 5, 6]
    DIE_X_TO_NOC_1_X = [9, 0, 8, 1, 7, 2, 6, 3, 5, 4]
    DIE_Y_TO_NOC_1_Y = [11, 0, 10, 1, 9, 2, 8, 3, 7, 4, 6, 5]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)
    NOC_1_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_1_X)
    NOC_1_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_1_Y)

    NOC0_X_TO_NOCTR_X = {
        0: 16,
        1: 18,
        2: 19,
        3: 20,
        4: 21,
        5: 17,
        6: 22,
        7: 23,
        8: 24,
        9: 25,
    }
    NOCTR_X_TO_NOC0_X = {v: k for k, v in NOC0_X_TO_NOCTR_X.items()}

    # The following is used to convert harvesting mask to NOC0 Y location. If harvesting mask bit 0 is set, then
    # the NOC0 Y location is 11. If harvesting mask bit 1 is set, then the NOC0 Y location is 1, etc...
    HARVESTING_NOC_LOCATIONS = [11, 1, 10, 2, 9, 3, 8, 4, 7, 5]

    PCI_ARC_RESET_BASE_ADDR = 0x1FF30000
    PCI_ARC_CSM_DATA_BASE_ADDR = 0x1FE80000
    PCI_ARC_ROM_DATA_BASE_ADDR = 0x1FF00000

    NOC_ARC_RESET_BASE_ADDR = 0x880030000
    NOC_ARC_CSM_DATA_BASE_ADDR = 0x810000000
    NOC_ARC_ROM_DATA_BASE_ADDR = 0x880000000

    EFUSE_PCI = 0x1FF42200
    EFUSE_JTAG_AXI = 0x80042200
    EFUSE_NOC = 0x880042200

    def get_harvested_noc0_y_rows(self):
        harvested_noc0_y_rows = []
        if self._harvesting:
            bitmask = self._harvesting["harvest_mask"]
            for h_index in range(0, self.row_count()):
                if (1 << h_index) & bitmask:  # Harvested
                    harvested_noc0_y_rows.append(self.HARVESTING_NOC_LOCATIONS[h_index])
        return harvested_noc0_y_rows

    # Coordinate conversion functions (see tt_coordinate.py for description of coordinate systems)
    def noc0_to_tensix(self, loc):
        if isinstance(loc, OnChipCoordinate):
            noc0_x, noc0_y = loc._noc0_coord
        else:
            noc0_x, noc0_y = loc
        if noc0_x == 0 or noc0_x == 5:
            raise CoordinateTranslationError("NOC0 x=0 and x=5 do not have an RC coordinate")
        if noc0_y == 0 or noc0_y == 6:
            raise CoordinateTranslationError("NOC0 y=0 and y=6 do not have an RC coordinate")
        row = noc0_y - 1
        col = noc0_x - 1
        if noc0_x > 5:
            col -= 1
        if noc0_y > 6:
            row -= 1
        return row, col

    def tensix_to_noc0(self, netlist_loc):
        row, col = netlist_loc
        noc0_y = row + 1
        noc0_x = col + 1
        if noc0_x >= 5:
            noc0_x += 1
        if noc0_y >= 6:
            noc0_y += 1
        return noc0_x, noc0_y

    def _handle_harvesting_for_nocTr_noc0_map(self, num_harvested_rows):
        # 1. Handle Ethernet rows
        self.nocTr_y_to_noc0_y[16] = 0
        self.nocTr_y_to_noc0_y[17] = 6

        # 2. Handle non-harvested rows
        harvested_noc0_y_rows = self.get_harvested_noc0_y_rows()

        nocTr_y = 18
        for noc0_y in range(0, self.row_count()):
            if noc0_y in harvested_noc0_y_rows or noc0_y == 0 or noc0_y == 6:
                pass  # Skip harvested rows and Ethernet rows
            else:
                self.nocTr_y_to_noc0_y[nocTr_y] = noc0_y
                nocTr_y += 1

        # 3. Handle harvested rows
        for netlist_row in range(0, num_harvested_rows):
            self.nocTr_y_to_noc0_y[16 + self.row_count() - num_harvested_rows + netlist_row] = harvested_noc0_y_rows[
                netlist_row
            ]

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            device_desc_path,
            context,
        )

    def row_count(self):
        return len(WormholeDevice.DIE_Y_TO_NOC_0_Y)

    def get_tensix_configuration_register_base(self) -> int:
        return 0xFFEF0000

    __configuration_register_map = {
        "ALU_FORMAT_SPEC_REG2_Dstacc": tt_device.TensixRegisterDescription(address=1 * 4, mask=0x1E000000, shift=25),
        "ALU_ACC_CTRL_Fp32_enabled": tt_device.TensixRegisterDescription(address=1 * 4, mask=0x20000000, shift=29),
        "DISABLE_RISC_BP_Disable_main": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x400000, shift=22),
        "DISABLE_RISC_BP_Disable_trisc": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x3800000, shift=23),
        "DISABLE_RISC_BP_Disable_ncrisc": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x4000000, shift=26),
        "RISCV_IC_INVALIDATE_InvalidateAll": tt_device.TensixRegisterDescription(address=157 * 4, mask=0x1F, shift=0),
        "TRISC_RESET_PC_SEC0_PC": tt_device.TensixRegisterDescription(address=158 * 4, mask=0xFFFFFFFF, shift=0),
        "TRISC_RESET_PC_SEC1_PC": tt_device.TensixRegisterDescription(address=159 * 4, mask=0xFFFFFFFF, shift=0),
        "TRISC_RESET_PC_SEC2_PC": tt_device.TensixRegisterDescription(address=160 * 4, mask=0xFFFFFFFF, shift=0),
        "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": tt_device.TensixRegisterDescription(
            address=161 * 4, mask=0x7, shift=0
        ),
        "NCRISC_RESET_PC_PC": tt_device.TensixRegisterDescription(address=162 * 4, mask=0xFFFFFFFF, shift=0),
        "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": tt_device.TensixRegisterDescription(
            address=163 * 4, mask=0x1, shift=0
        ),
    }

    def get_configuration_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in WormholeDevice.__configuration_register_map:
            return WormholeDevice.__configuration_register_map[register_name]
        return None

    def get_tenxis_debug_register_base(self) -> int:
        return 0xFFB12000

    __debug_register_map = {
        "RISCV_DEBUG_REG_CFGREG_RD_CNTL": tt_device.TensixRegisterDescription(address=0x58, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_DBG_RD_DATA": tt_device.TensixRegisterDescription(address=0x5C, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_CFGREG_RDDATA": tt_device.TensixRegisterDescription(address=0x78, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_DBG_ARRAY_RD_EN": tt_device.TensixRegisterDescription(address=0x60, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_DBG_ARRAY_RD_CMD": tt_device.TensixRegisterDescription(address=0x64, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_DBG_ARRAY_RD_DATA": tt_device.TensixRegisterDescription(
            address=0x6C, mask=0xFFFFFFFF, shift=0
        ),
        "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": tt_device.TensixRegisterDescription(address=0x80, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": tt_device.TensixRegisterDescription(address=0x84, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": tt_device.TensixRegisterDescription(
            address=0x88, mask=0xFFFFFFFF, shift=0
        ),
        "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": tt_device.TensixRegisterDescription(
            address=0x8C, mask=0xFFFFFFFF, shift=0
        ),
        "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL0": tt_device.TensixRegisterDescription(
            address=0xA0, mask=0xFFFFFFFF, shift=0
        ),
        "RISCV_DEBUG_REG_DBG_INSTRN_BUF_CTRL1": tt_device.TensixRegisterDescription(
            address=0xA4, mask=0xFFFFFFFF, shift=0
        ),
        "RISCV_DEBUG_REG_DBG_INSTRN_BUF_STATUS": tt_device.TensixRegisterDescription(
            address=0xA8, mask=0xFFFFFFFF, shift=0
        ),
        "RISCV_DEBUG_REG_SOFT_RESET_0": tt_device.TensixRegisterDescription(address=0x1B0, mask=0xFFFFFFFF, shift=0),
    }

    def get_debug_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in WormholeDevice.__debug_register_map:
            return WormholeDevice.__debug_register_map[register_name]
        return None
