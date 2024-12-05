# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0


# TODO: This is plain copy of tt_blackhole.py. Need to update this file with Quasar specific details
from ttlens import tt_util as util
from ttlens import tt_device
from ttlens.tt_coordinate import CoordinateTranslationError, OnChipCoordinate

#
# Device
#
class QuasarDevice(tt_device.Device):
    # Physical location mapping. Physical coordinates are the geografical coordinates on a chip's die.
    # DIE_X_TO_NOC_0_X = [0, 1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10, 8, 9]
    # DIE_Y_TO_NOC_0_Y = [0, 1, 11, 2, 10, 3, 9, 4, 8, 5, 7, 6]
    # DIE_X_TO_NOC_1_X = [16, 15, 0, 14, 1, 13, 2, 12, 3, 11, 4, 10, 5, 9, 6, 8, 7]
    # DIE_Y_TO_NOC_1_Y = [11, 10, 0, 9, 1, 8, 2, 7, 3, 6, 4, 5]
    # NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    # NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)
    # NOC_1_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_1_X)
    # NOC_1_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_1_Y)

    # TODO: Translated coordinates are not correct in quasar. We need to understand what is happening to them since there are three columns now that are not tensix compared to two in wormhole. For now just an identity mapping
    NOC0_X_TO_NOCTR_X = {i: i for i in range(0, 100)}
    NOCTR_X_TO_NOC0_X = {v: k for k, v in NOC0_X_TO_NOCTR_X.items()}

    # TODO (#90): Harvesting is different in blackhole. Both x and y can be harvested... For now, similar as in grayskull..
    def get_harvested_noc0_y_rows(self):
        harvested_workers = self._block_locations["harvested_workers"]
        return list({y for x, y in harvested_workers})

    # Coordinate conversion functions (see tt_coordinate.py for description of coordinate systems)
    def noc0_to_tensix(self, loc):
        if isinstance(loc, OnChipCoordinate):
            noc0_x, noc0_y = loc._noc0_coord
        else:
            noc0_x, noc0_y = loc
        if noc0_x == 0 or noc0_x == 8 or noc0_x == 9:
            raise CoordinateTranslationError(
                "NOC0 x=0 and x=8 and x=9 do not have an RC coordinate"
            )
        if noc0_y == 0 or noc0_y == 1:
            raise CoordinateTranslationError(
                "NOC0 y=0 and y=1 do not have an RC coordinate"
            )
        row = noc0_y - 2
        col = noc0_x - 1
        if noc0_x > 9:
            col -= 2
        return row, col

    def tensix_to_noc0(self, netlist_loc):
        row, col = netlist_loc
        noc0_y = row + 2
        noc0_x = col + 1
        if noc0_x >= 9:
            noc0_x += 2
        return noc0_x, noc0_y

    # TODO: Harvesting is different in quasar. Both x and y can be harvested... For now, just an identity mapping
    def _handle_harvesting_for_nocTr_noc0_map(self, num_harvested_rows):
        self.nocTr_x_to_noc0_x = {i: i for i in range(0, self.row_count())}

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(id, arch, cluster_desc, {}, device_desc_path, context)

    def get_tensix_configuration_register_base(self) -> int:
        return 0xFFEF0000

    __configuration_register_map = {
        # 'DISABLE_RISC_BP_Disable_main': tt_device.TensixRegisterDescription(address=2 * 4, mask=0x400000, shift=22),
        # 'DISABLE_RISC_BP_Disable_trisc': tt_device.TensixRegisterDescription(address=2 * 4, mask=0x3800000, shift=23),
        # 'DISABLE_RISC_BP_Disable_ncrisc': tt_device.TensixRegisterDescription(address=2 * 4, mask=0x4000000, shift=26),
        # 'RISCV_IC_INVALIDATE_InvalidateAll': tt_device.TensixRegisterDescription(address=185 * 4, mask=0x1f, shift=0),
    }

    def get_configuration_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in QuasarDevice.__configuration_register_map:
            return QuasarDevice.__configuration_register_map[register_name]
        return None

    def get_tenxis_debug_register_base(self) -> int:
        return 0x800000

    __debug_register_map = {
        'RISCV_DEBUG_REG_RISC_DBG_CNTL_0': tt_device.TensixRegisterDescription(address=0x60, mask=0xffffffff, shift=0),
        'RISCV_DEBUG_REG_RISC_DBG_CNTL_1': tt_device.TensixRegisterDescription(address=0x64, mask=0xffffffff, shift=0),
        'RISCV_DEBUG_REG_RISC_DBG_STATUS_0': tt_device.TensixRegisterDescription(address=0x68, mask=0xffffffff, shift=0),
        'RISCV_DEBUG_REG_RISC_DBG_STATUS_1': tt_device.TensixRegisterDescription(address=0x6C, mask=0xffffffff, shift=0),
        'RISCV_DEBUG_REG_SOFT_RESET_0': tt_device.TensixRegisterDescription(address=0xC4, mask=0xffffffff, shift=0),
        # 'TRISC_RESET_PC_SEC0_PC': tt_device.TensixRegisterDescription(address=0x228, mask=0xffffffff, shift=0), # Old name from configuration register
        # 'RISCV_DEBUG_REG_TRISC0_RESET_PC': tt_device.TensixRegisterDescription(address=0x228, mask=0xffffffff, shift=0), # New name
        # 'TRISC_RESET_PC_SEC1_PC': tt_device.TensixRegisterDescription(address=0x22c, mask=0xffffffff, shift=0), # Old name from configuration register
        # 'RISCV_DEBUG_REG_TRISC1_RESET_PC': tt_device.TensixRegisterDescription(address=0x22c, mask=0xffffffff, shift=0), # New name
        # 'TRISC_RESET_PC_SEC2_PC': tt_device.TensixRegisterDescription(address=0x230, mask=0xffffffff, shift=0), # Old name from configuration register
        # 'RISCV_DEBUG_REG_TRISC2_RESET_PC': tt_device.TensixRegisterDescription(address=0x230, mask=0xffffffff, shift=0), # New name
        # 'TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en': tt_device.TensixRegisterDescription(address=0x234, mask=0x7, shift=0), # Old name from configuration register
        # 'RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE': tt_device.TensixRegisterDescription(address=0x234, mask=0x7, shift=0), # New name
        # 'NCRISC_RESET_PC_PC': tt_device.TensixRegisterDescription(address=0x238, mask=0xffffffff, shift=0), # Old name from configuration register
        # 'RISCV_DEBUG_REG_NCRISC_RESET_PC': tt_device.TensixRegisterDescription(address=0x238, mask=0xffffffff, shift=0), # New name
        # 'NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en': tt_device.TensixRegisterDescription(address=0x23c, mask=0x1, shift=0), # Old name from configuration register
        # 'RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE': tt_device.TensixRegisterDescription(address=0x23c, mask=0x1, shift=0), # New name
    }

    def get_debug_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in QuasarDevice.__debug_register_map:
            return QuasarDevice.__debug_register_map[register_name]
        return None
