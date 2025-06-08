# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0


# TODO: This is plain copy of blackhole.py. Need to update this file with Quasar specific details
from functools import cache
from ttexalens import util
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import (
    Device,
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    TensixRegisterDescription,
)
from ttexalens.hardware.noc_block import NocBlock
from ttexalens.hardware.quasar.functional_worker_block import QuasarFunctionalWorkerBlock

#
# Device
#
class QuasarDevice(Device):
    # TODO: Physical location mapping. Physical coordinates are the geografical coordinates on a chip's die.
    DIE_X_TO_NOC_0_X = [0, 1, 16, 2, 15, 3, 14, 4, 13, 5, 12, 6, 11, 7, 10, 8, 9]
    DIE_Y_TO_NOC_0_Y = [0, 1, 11, 2, 10, 3, 9, 4, 8, 5, 7, 6]
    DIE_X_TO_NOC_1_X = [16, 15, 0, 14, 1, 13, 2, 12, 3, 11, 4, 10, 5, 9, 6, 8, 7]
    DIE_Y_TO_NOC_1_Y = [11, 10, 0, 9, 1, 8, 2, 7, 3, 6, 4, 5]
    NOC_0_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_0_X)
    NOC_0_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_0_Y)
    NOC_1_X_TO_DIE_X = util.reverse_mapping_list(DIE_X_TO_NOC_1_X)
    NOC_1_Y_TO_DIE_Y = util.reverse_mapping_list(DIE_Y_TO_NOC_1_Y)

    # Register base addresses (Neo 0)
    CONFIGURATION_REGISTER_BASE = 0x0080A000
    DEBUG_REGISTER_BASE = 0x00800000

    # # Register base addresses (Neo 1)
    # CONFIGURATION_REGISTER_BASE = 0x0081A000
    # DEBUG_REGISTER_BASE = 0x00810000

    # # Register base addresses (Neo 2)
    # CONFIGURATION_REGISTER_BASE = 0x0082A000
    # DEBUG_REGISTER_BASE = 0x00820000

    # # Register base addresses (Neo 3)
    # CONFIGURATION_REGISTER_BASE = 0x0083A000
    # DEBUG_REGISTER_BASE = 0x00830000

    # NOC_CONTROL_REGISTER_BASE = 0xFFB20000
    # NOC_CONFIGURATION_REGISTER_BASE = 0xFFB20100
    # NOC_STATUS_REGISTER_BASE = 0xFFB20200

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(id, arch, cluster_desc, device_desc_path, context)

    def _get_tensix_register_description(self, register_name: str) -> TensixRegisterDescription | None:
        """Overrides the base class method to provide register descriptions for Blackhole device."""
        if register_name in QuasarDevice.__register_map:
            return QuasarDevice.__register_map[register_name]
        else:
            return None

    def _get_tensix_register_base_address(self, register_description: TensixRegisterDescription) -> int | None:
        """Overrides the base class method to provide register base addresses for Blackhole device."""
        if isinstance(register_description, ConfigurationRegisterDescription):
            return QuasarDevice.CONFIGURATION_REGISTER_BASE
        elif isinstance(register_description, DebugRegisterDescription):
            return QuasarDevice.DEBUG_REGISTER_BASE
        # elif isinstance(register_description, NocControlRegisterDescription):
        #     return QuasarDevice.NOC_CONTROL_REGISTER_BASE
        # elif isinstance(register_description, NocConfigurationRegisterDescription):
        #     return QuasarDevice.NOC_CONFIGURATION_REGISTER_BASE
        # elif isinstance(register_description, NocStatusRegisterDescription):
        #     return QuasarDevice.NOC_STATUS_REGISTER_BASE
        else:
            return None

    __register_map = {
        # 'DISABLE_RISC_BP_Disable_main': tt_device.TensixRegisterDescription(address=2 * 4, mask=0x400000, shift=22),
        # 'DISABLE_RISC_BP_Disable_trisc': tt_device.TensixRegisterDescription(address=2 * 4, mask=0x3800000, shift=23),
        # 'DISABLE_RISC_BP_Disable_ncrisc': tt_device.TensixRegisterDescription(address=2 * 4, mask=0x4000000, shift=26),
        # 'RISCV_IC_INVALIDATE_InvalidateAll': tt_device.TensixRegisterDescription(address=185 * 4, mask=0x1f, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": DebugRegisterDescription(address=0x60, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": DebugRegisterDescription(address=0x64, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": DebugRegisterDescription(address=0x68, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": DebugRegisterDescription(address=0x6C, mask=0xFFFFFFFF, shift=0),
        "RISCV_DEBUG_REG_SOFT_RESET_0": DebugRegisterDescription(address=0xC4, mask=0xFFFFFFFF, shift=0),
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

    @cache
    def get_block(self, location: OnChipCoordinate) -> NocBlock:
        block_type = self.get_block_type(location)
        if block_type == "functional_workers":
            return QuasarFunctionalWorkerBlock(location)
        raise ValueError(f"Unsupported block type: {block_type}")
