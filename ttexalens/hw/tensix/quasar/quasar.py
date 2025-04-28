# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0


# TODO: This is plain copy of blackhole.py. Need to update this file with Quasar specific details
from ttexalens import util
from ttexalens.coordinate import OnChipCoordinate
from ttexalens.device import (
    Device,
    ConfigurationRegisterDescription,
    DebugRegisterDescription,
    TensixRegisterDescription,
    DebugBusSignalDescription,
)
from typing import List

from ttexalens.tt_exalens_lib import read_word_from_device, write_words_to_device

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

    RISC_NAME_TO_ID = { "TRISC0": 0, "TRISC1": 1, "TRISC2": 2, "TRISC3": 3}

    # Register base addresses (Neo 0)
    CONFIGURATION_REGISTER_BASE = 0x1820000
    DEBUG_REGISTER_BASE = 0x01800000
    RISC_START_ADDRESS = { "TRISC0": 0x00006000, "TRISC1": 0x0000a000, "TRISC2": 0x0000e000, "TRISC3": 0x00012000 }

    # # Register base addresses (Neo 1)
    # CONFIGURATION_REGISTER_BASE = 0x0181A000
    # DEBUG_REGISTER_BASE = 0x01810000
    # RISC_START_ADDRESS = { "TRISC0": 0x00016000, "TRISC1": 0x0001a000, "TRISC2": 0x0001e000, "TRISC3": 0x00022000 }

    # # Register base addresses (Neo 2)
    # CONFIGURATION_REGISTER_BASE = 0x0182A000
    # DEBUG_REGISTER_BASE = 0x01820000
    # RISC_START_ADDRESS = { "TRISC0": 0x00026000, "TRISC1": 0x0002a000, "TRISC2": 0x0002e000, "TRISC3": 0x00032000 }

    # # Register base addresses (Neo 3)
    # CONFIGURATION_REGISTER_BASE = 0x0183A000
    # DEBUG_REGISTER_BASE = 0x01830000
    # RISC_START_ADDRESS = { "TRISC0": 0x00036000, "TRISC1": 0x0003a000, "TRISC2": 0x0003e000, "TRISC3": 0x00042000 }

    # NOC_CONTROL_REGISTER_BASE = 0xFFB20000
    # NOC_CONFIGURATION_REGISTER_BASE = 0xFFB20100
    # NOC_STATUS_REGISTER_BASE = 0xFFB20200

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(id, arch, cluster_desc, device_desc_path, context)

    def _get_tensix_register_description(self, register_name: str) -> TensixRegisterDescription:
        """Overrides the base class method to provide register descriptions for Blackhole device."""
        if register_name in QuasarDevice.__register_map:
            return QuasarDevice.__register_map[register_name]
        else:
            return None

    def _get_tensix_register_base_address(self, register_description: TensixRegisterDescription) -> int:
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
        "RISCV_DEBUG_REG_DBG_BUS_CNTL_REG": DebugRegisterDescription(address=0x28),
        "RISCV_DEBUG_REG_CFGREG_RD_CNTL": DebugRegisterDescription(address=0x2C),
        "RISCV_DEBUG_REG_DBG_RD_DATA": DebugRegisterDescription(address=0x30),
        "DISABLE_RISC_BP_Disable_trisc": DebugRegisterDescription(address=0x260, mask=0xf, shift=0), # Old name from previous architectures
        "RISC_BRANCH_PREDICTION_CTRL": DebugRegisterDescription(address=0x260, mask=0xf, shift=0), # New name
        "RISCV_IC_INVALIDATE_InvalidateAll": DebugRegisterDescription(address=0x248, mask=0xf, shift=0),
        "RISCV_DEBUG_REG_RISC_DBG_CNTL_0": DebugRegisterDescription(address=0x54),
        "RISCV_DEBUG_REG_RISC_DBG_CNTL_1": DebugRegisterDescription(address=0x58),
        "RISCV_DEBUG_REG_RISC_DBG_STATUS_0": DebugRegisterDescription(address=0x5C),
        "RISCV_DEBUG_REG_RISC_DBG_STATUS_1": DebugRegisterDescription(address=0x60),
        "RISCV_DEBUG_REG_SOFT_RESET_0": DebugRegisterDescription(address=0xB0),
        'TRISC_RESET_PC_SEC0_PC': DebugRegisterDescription(address=0xF8), # Old name from configuration register
        'RISCV_DEBUG_REG_TRISC0_RESET_PC': DebugRegisterDescription(address=0xF8), # New name
        'TRISC_RESET_PC_SEC1_PC': DebugRegisterDescription(address=0xFC), # Old name from configuration register
        'RISCV_DEBUG_REG_TRISC1_RESET_PC': DebugRegisterDescription(address=0xFC), # New name
        'TRISC_RESET_PC_SEC2_PC': DebugRegisterDescription(address=0x100), # Old name from configuration register
        'RISCV_DEBUG_REG_TRISC2_RESET_PC': DebugRegisterDescription(address=0x100), # New name
        'TRISC_RESET_PC_SEC3_PC': DebugRegisterDescription(address=0x104), # Old name from configuration register
        'RISCV_DEBUG_REG_TRISC3_RESET_PC': DebugRegisterDescription(address=0x104), # New name
        'TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en': DebugRegisterDescription(address=0x108, mask=0xF, shift=0), # Old name from configuration register
        'RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE': DebugRegisterDescription(address=0x108, mask=0xF, shift=0), # New name
    }

    def _get_debug_bus_signal_description(self, name):
        """Overrides the base class method to provide debug bus signal descriptions for Wormhole device."""
        if name in QuasarDevice.__debug_bus_signal_map:
            return QuasarDevice.__debug_bus_signal_map[name]
        return None

    # TODO: Should be copied from Blackhole. Current values are only for debugging purposes.
    __debug_bus_signal_map = {
        # For the other signals applying the pc_mask.
        "trisc0_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 5 + 1, mask=0x3FFFFFFF),
        "trisc1_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 6 + 1, mask=0x3FFFFFFF),
        "trisc2_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 7 + 1, mask=0x3FFFFFFF),
        "trisc3_pc": DebugBusSignalDescription(rd_sel=1, daisy_sel=7, sig_sel=2 * 8 + 1, mask=0x3FFFFFFF),
    }

    def get_debug_bus_signal_names(self) -> List[str]:
        return list(self.__debug_bus_signal_map.keys())

    # TODO: Should be removed, it was for debugging why reading debug bus fails
    def read_debug_bus_signal_from_description(self, loc: OnChipCoordinate, signal: DebugBusSignalDescription) -> int:
        if signal is None:
            raise ValueError(f"Debug Bus signal description is not defined")

        # Write the configuration
        en = 1
        config_addr = self.get_tensix_register_address("RISCV_DEBUG_REG_DBG_BUS_CNTL_REG")
        config = (en << 29) | (signal.rd_sel << 25) | (signal.daisy_sel << 16) | (signal.sig_sel << 0)
        write_words_to_device(loc, config_addr, config, self._id)

        # Read the data
        data_addr = self.get_tensix_register_address("RISCV_DEBUG_REG_DBG_RD_DATA")
        data = read_word_from_device(loc, data_addr)

        # Disable the signal
        write_words_to_device(loc, config_addr, 0, self._id)

        return data if signal.mask is None else data & signal.mask
