# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0


# TODO (#75): This is plain copy of tt_wormhole.py. Need to update this file with Blackhole specific details
from ttlens import tt_util as util
from ttlens import tt_device
from ttlens.tt_coordinate import CoordinateTranslationError, OnChipCoordinate
from ttlens.tt_lens_lib import read_word_from_device

class BlackholeL1AddressMap(tt_device.L1AddressMap):
    def __init__(self):
        super().__init__()

        ## Taken from l1_address_map.h. Ideally make this auto-generated
        self._l1_address_map = dict()
        self._l1_address_map["trisc0"] = tt_device.BinarySlot(
            offset_bytes=0 + 20 * 1024 + 32 * 1024, size_bytes=20 * 1024
        )
        self._l1_address_map["trisc1"] = tt_device.BinarySlot(
            offset_bytes=self._l1_address_map["trisc0"].offset_bytes + self._l1_address_map["trisc0"].size_bytes,
            size_bytes=16 * 1024,
        )
        self._l1_address_map["trisc2"] = tt_device.BinarySlot(
            offset_bytes=self._l1_address_map["trisc1"].offset_bytes + self._l1_address_map["trisc1"].size_bytes,
            size_bytes=20 * 1024,
        )
        # Brisc, ncrisc, to be added


class BlackholeDRAMEpochCommandAddressMap(tt_device.L1AddressMap):
    def __init__(self):
        super().__init__()

        ## Taken from dram_address_map.h. Ideally make this auto-generated
        self._l1_address_map = dict()
        self._l1_address_map["trisc0"] = tt_device.BinarySlot(offset_bytes=-1, size_bytes=20 * 1024)
        self._l1_address_map["trisc1"] = tt_device.BinarySlot(offset_bytes=-1, size_bytes=16 * 1024)
        self._l1_address_map["trisc2"] = tt_device.BinarySlot(offset_bytes=-1, size_bytes=20 * 1024)
        # Brisc, ncrisc, to be added


class BlackholeEthL1AddressMap(tt_device.L1AddressMap):
    def __init__(self):
        super().__init__()

        ## Taken from l1_address_map.h. Ideally make this auto-generated
        self._l1_address_map = dict()
        # erisc, erisc-app to be added


#
# Device
#
class BlackholeDevice(tt_device.Device):
    SIG_SEL_CONST = 5  # TODO (#75): Unknown constant!!!!
    # IMPROVE: some of this can be read from architecture yaml file
    DRAM_CHANNEL_TO_NOC0_LOC = [(0, 11), (0, 2), (0, 8), (0, 5), (9, 11), (9, 2), (9, 8), (9, 5)]

    # Physical location mapping. Physical coordinates are the geografical coordinates on a chip's die.
    DIE_X_TO_NOC_0_X = [0, 1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10, 8, 9]
    DIE_Y_TO_NOC_0_Y = [0, 1, 11, 2, 10, 3, 9, 4, 8, 5, 7, 6]
    DIE_X_TO_NOC_1_X = [16, 15, 0, 14, 1, 13, 2, 12, 3, 11, 4, 10, 5, 9, 6, 8, 7]
    DIE_Y_TO_NOC_1_Y = [11, 10, 0, 9, 1, 8, 2, 7, 3, 6, 4, 5]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)
    NOC_1_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_1_X)
    NOC_1_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_1_Y)

    PCI_ARC_RESET_BASE_ADDR = 0x1FF30000
    PCI_ARC_CSM_DATA_BASE_ADDR = 0x1FE80000
    PCI_ARC_ROM_DATA_BASE_ADDR = 0x1FF00000

    NOC_ARC_RESET_BASE_ADDR = 0x80030000
    NOC_ARC_CSM_DATA_BASE_ADDR = 0x10000000
    NOC_ARC_ROM_DATA_BASE_ADDR = 0x80000000

    # TODO (#89): Translated coordinates are not correct in blackhole. We need to understand what is happening to them since there are three columns now that are not tensix compared to two in wormhole. For now just an identity mapping
    NOC0_X_TO_NOCTR_X = {i: i for i in range(0, len(NOC_0_X_TO_DIE_X))}
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
            raise CoordinateTranslationError("NOC0 x=0 and x=8 and x=9 do not have an RC coordinate")
        if noc0_y == 0 or noc0_y == 1:
            raise CoordinateTranslationError("NOC0 y=0 and y=1 do not have an RC coordinate")
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

    # TODO (#90): Harvesting is different in blackhole. Both x and y can be harvested... For now, just an identity mapping
    def _handle_harvesting_for_nocTr_noc0_map(self, num_harvested_rows):
        self.nocTr_x_to_noc0_x = {i: i for i in range(0, self.row_count())}

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            {
                "functional_workers": BlackholeL1AddressMap(),
                "eth": BlackholeEthL1AddressMap(),
                "dram": BlackholeDRAMEpochCommandAddressMap(),
            },
            device_desc_path,
            context,
        )

    def row_count(self):
        return len(BlackholeDevice.DIE_Y_TO_NOC_0_Y)

    def get_tensix_configuration_register_base(self) -> int:
        return 0xFFEF0000

    __configuration_register_map = {
        "DISABLE_RISC_BP_Disable_main": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x400000, shift=22),
        "DISABLE_RISC_BP_Disable_trisc": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x3800000, shift=23),
        "DISABLE_RISC_BP_Disable_ncrisc": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x4000000, shift=26),
        "RISCV_IC_INVALIDATE_InvalidateAll": tt_device.TensixRegisterDescription(address=185 * 4, mask=0x1F, shift=0),
    }

    def get_configuration_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in BlackholeDevice.__configuration_register_map:
            return BlackholeDevice.__configuration_register_map[register_name]
        return None

    def get_tenxis_debug_register_base(self) -> int:
        return 0xFFB12000

    __debug_register_map = {
        "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": tt_device.TensixRegisterDescription(address=0x80, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": tt_device.TensixRegisterDescription(address=0x84, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": tt_device.TensixRegisterDescription(
            address=0x88, mask=0xFFFFFFFF, shift=0
        ),
        "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": tt_device.TensixRegisterDescription(
            address=0x8C, mask=0xFFFFFFFF, shift=0
        ),
        "RISCV_DEBUG_REG_SOFT_RESET_0": tt_device.TensixRegisterDescription(address=0x1B0, mask=0xFFFFFFFF, shift=0),
        "TRISC_RESET_PC_SEC0_PC": tt_device.TensixRegisterDescription(
            address=0x228, mask=0xFFFFFFFF, shift=0
        ),  # Old name from configuration register
        "RISCV_DEBUG_REG_TRISC0_RESET_PC": tt_device.TensixRegisterDescription(
            address=0x228, mask=0xFFFFFFFF, shift=0
        ),  # New name
        "TRISC_RESET_PC_SEC1_PC": tt_device.TensixRegisterDescription(
            address=0x22C, mask=0xFFFFFFFF, shift=0
        ),  # Old name from configuration register
        "RISCV_DEBUG_REG_TRISC1_RESET_PC": tt_device.TensixRegisterDescription(
            address=0x22C, mask=0xFFFFFFFF, shift=0
        ),  # New name
        "TRISC_RESET_PC_SEC2_PC": tt_device.TensixRegisterDescription(
            address=0x230, mask=0xFFFFFFFF, shift=0
        ),  # Old name from configuration register
        "RISCV_DEBUG_REG_TRISC2_RESET_PC": tt_device.TensixRegisterDescription(
            address=0x230, mask=0xFFFFFFFF, shift=0
        ),  # New name
        "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": tt_device.TensixRegisterDescription(
            address=0x234, mask=0x7, shift=0
        ),  # Old name from configuration register
        "RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE": tt_device.TensixRegisterDescription(
            address=0x234, mask=0x7, shift=0
        ),  # New name
        "NCRISC_RESET_PC_PC": tt_device.TensixRegisterDescription(
            address=0x238, mask=0xFFFFFFFF, shift=0
        ),  # Old name from configuration register
        "RISCV_DEBUG_REG_NCRISC_RESET_PC": tt_device.TensixRegisterDescription(
            address=0x238, mask=0xFFFFFFFF, shift=0
        ),  # New name
        "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": tt_device.TensixRegisterDescription(
            address=0x23C, mask=0x1, shift=0
        ),  # Old name from configuration register
        "RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE": tt_device.TensixRegisterDescription(
            address=0x23C, mask=0x1, shift=0
        ),  # New name
    }

    def get_debug_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in BlackholeDevice.__debug_register_map:
            return BlackholeDevice.__debug_register_map[register_name]
        return None
