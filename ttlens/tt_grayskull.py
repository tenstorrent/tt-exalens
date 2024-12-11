# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0
from ttlens import tt_util as util
from ttlens import tt_device


class GrayskullL1AddressMap(tt_device.L1AddressMap):
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


class GrayskullDRAMEpochCommandAddressMap(tt_device.L1AddressMap):
    def __init__(self):
        super().__init__()

        ## Taken from dram_address_map.h. Ideally make this auto-generated
        self._l1_address_map = dict()
        self._l1_address_map["trisc0"] = tt_device.BinarySlot(offset_bytes=-1, size_bytes=20 * 1024)
        self._l1_address_map["trisc1"] = tt_device.BinarySlot(offset_bytes=-1, size_bytes=16 * 1024)
        self._l1_address_map["trisc2"] = tt_device.BinarySlot(offset_bytes=-1, size_bytes=20 * 1024)
        # Brisc, ncrisc, to be added


#
# Device
#
class GrayskullDevice(tt_device.Device):
    SIG_SEL_CONST = 9
    # Some of this can be read from architecture yaml file
    DRAM_CHANNEL_TO_NOC0_LOC = [
        (1, 0),
        (1, 6),
        (4, 0),
        (4, 6),
        (7, 0),
        (7, 6),
        (10, 0),
        (10, 6),
    ]

    # Physical location mapping
    DIE_X_TO_NOC_0_X = [0, 12, 1, 11, 2, 10, 3, 9, 4, 8, 5, 7, 6]
    DIE_Y_TO_NOC_0_Y = [0, 11, 1, 10, 2, 9, 3, 8, 4, 7, 5, 6]
    DIE_X_TO_NOC_1_X = [12, 0, 11, 1, 10, 2, 9, 3, 8, 4, 7, 5, 6]
    DIE_Y_TO_NOC_1_Y = [11, 0, 10, 1, 9, 2, 8, 3, 7, 4, 6, 5]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)
    NOC_1_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_1_X)
    NOC_1_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_1_Y)

    # Just an identity mapping
    NOC0_X_TO_NOCTR_X = {i: i for i in range(0, len(NOC_0_X_TO_DIE_X))}
    NOCTR_X_TO_NOC0_X = {v: k for k, v in NOC0_X_TO_NOCTR_X.items()}

    PCI_ARC_RESET_BASE_ADDR = 0x1FF30000
    PCI_ARC_CSM_DATA_BASE_ADDR = 0x1FE80000
    PCI_ARC_ROM_DATA_BASE_ADDR = 0x1FF00000

    EFUSE_PCI = 0x1FF40200
    EFUSE_JTAG_AXI = 0x80040200
    EFUSE_NOC = 0x80040200

    def get_harvested_noc0_y_rows(self):
        harvested_workers = self._block_locations["harvested_workers"]
        return list({y for x, y in harvested_workers})

    def noc0_to_tensix(self, noc0_loc):
        noc0_x, noc0_y = noc0_loc
        if noc0_y == 0 or noc0_y == 6:
            assert False, "NOC0 y=0 and y=6 do not have an RC coordinate"
        if noc0_x == 0:
            assert False, "NOC0 x=0 does not have an RC coordinate"
        row = noc0_y - 1
        col = noc0_x - 1
        if noc0_y > 6:
            row -= 1
        return row, col

    def tensix_to_noc0(self, netlist_loc):
        row, col = netlist_loc
        noc0_y = row + 1
        noc0_x = col + 1
        if noc0_y > 5:
            noc0_y += 1  # DRAM at noc0 Y coord of 6 is a hole in RC coordinates
        return noc0_x, noc0_y

    def _handle_harvesting_for_nocTr_noc0_map(self, num_harvested_rows):
        self.nocTr_x_to_noc0_x = {i: i for i in range(0, self.row_count())}

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(
            id,
            arch,
            cluster_desc,
            {"functional_workers": GrayskullL1AddressMap(), "dram": GrayskullDRAMEpochCommandAddressMap()},
            device_desc_path,
            context,
        )

    def row_count(self):
        return len(GrayskullDevice.DIE_Y_TO_NOC_0_Y)

    def get_tensix_configuration_register_base(self) -> int:
        return 0xFFEF0000

    __configuration_register_map = {
        "DISABLE_RISC_BP_Disable_main": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x100000, shift=20),
        "DISABLE_RISC_BP_Disable_trisc": tt_device.TensixRegisterDescription(address=2 * 4, mask=0xE00000, shift=21),
        "DISABLE_RISC_BP_Disable_ncrisc": tt_device.TensixRegisterDescription(address=2 * 4, mask=0x1000000, shift=24),
        "RISCV_IC_INVALIDATE_InvalidateAll": tt_device.TensixRegisterDescription(address=177 * 4, mask=0x1F, shift=0),
        "TRISC_RESET_PC_SEC0_PC": tt_device.TensixRegisterDescription(address=178 * 4, mask=0xFFFFFFFF, shift=0),
        "TRISC_RESET_PC_SEC1_PC": tt_device.TensixRegisterDescription(address=179 * 4, mask=0xFFFFFFFF, shift=0),
        "TRISC_RESET_PC_SEC2_PC": tt_device.TensixRegisterDescription(address=180 * 4, mask=0xFFFFFFFF, shift=0),
        "TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": tt_device.TensixRegisterDescription(
            address=181 * 4, mask=0x7, shift=0
        ),
        "NCRISC_RESET_PC_PC": tt_device.TensixRegisterDescription(address=182 * 4, mask=0xFFFFFFFF, shift=0),
        "NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en": tt_device.TensixRegisterDescription(
            address=183 * 4, mask=0x1, shift=0
        ),
    }

    def get_configuration_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in GrayskullDevice.__configuration_register_map:
            return GrayskullDevice.__configuration_register_map[register_name]
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
    }

    def get_debug_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in GrayskullDevice.__debug_register_map:
            return GrayskullDevice.__debug_register_map[register_name]
        return None
