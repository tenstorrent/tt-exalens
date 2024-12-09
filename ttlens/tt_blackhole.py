# SPDX-FileCopyrightText: © 2024 Tenstorrent AI ULC

# SPDX-License-Identifier: Apache-2.0


# TODO (#75): This is plain copy of tt_wormhole.py. Need to update this file with Blackhole specific details
from ttlens import tt_util as util
from ttlens import tt_device
from ttlens.tt_coordinate import CoordinateTranslationError, OnChipCoordinate
from ttlens.tt_lens_lib import read_word_from_device

phase_state_map = {
    0: "PHASE_START",
    1: "PHASE_AUTO_CONFIG",
    2: "PHASE_AUTO_CONFIG_SENT",
    3: "PHASE_ADVANCE_WAIT",
    4: "PHASE_PREV_DATA_FLUSH_WAIT",
    5: "PHASE_FWD_DATA",
}

dest_state_map = {
    0: "DEST_IDLE",
    1: "DEST_REMOTE",
    2: "DEST_LOCAL_RDY_WAIT",
    3: "DEST_LOCAL_HS",
    4: "DEST_LOCAL",
    5: "DEST_ENDPOINT",
    6: "DEST_NO_FWD",
}

dest_ready_state_map = {
    0: "DEST_READY_IDLE",
    1: "DEST_READY_SEND_FIRST",
    2: "DEST_READY_WAIT_DATA",
    3: "DEST_READY_SEND_SECOND",
    4: "DEST_READY_FWD_DATA",
}

src_ready_state_map = {
    0: "SRC_READY_IDLE",
    1: "SRC_READY_WAIT_CFG",
    2: "SRC_READY_DEST_READY_TABLE_RD",
    3: "SRC_READY_SEND_UPDATE",
    4: "SRC_READY_WAIT_ALL_DESTS",
    5: "SRC_READY_FWD_DATA",
}

src_state_map = {0: "SRC_IDLE", 1: "SRC_REMOTE", 2: "SRC_LOCAL", 3: "SRC_ENDPOINT"}


class BlackholeL1AddressMap(tt_device.L1AddressMap):
    def __init__(self):
        super().__init__()

        ## Taken from l1_address_map.h. Ideally make this auto-generated
        self._l1_address_map = dict()
        self._l1_address_map["trisc0"] = tt_device.BinarySlot(offset_bytes = 0 + 20 * 1024 + 32 * 1024, size_bytes = 20 * 1024)
        self._l1_address_map["trisc1"] = tt_device.BinarySlot(offset_bytes = self._l1_address_map["trisc0"].offset_bytes + self._l1_address_map["trisc0"].size_bytes, size_bytes = 16 * 1024)
        self._l1_address_map["trisc2"] = tt_device.BinarySlot(offset_bytes = self._l1_address_map["trisc1"].offset_bytes + self._l1_address_map["trisc1"].size_bytes, size_bytes = 20 * 1024)
        # Brisc, ncrisc, to be added

class BlackholeDRAMEpochCommandAddressMap(tt_device.L1AddressMap):
    def __init__(self):
        super().__init__()
        
        ## Taken from dram_address_map.h. Ideally make this auto-generated
        self._l1_address_map = dict()
        self._l1_address_map["trisc0"] = tt_device.BinarySlot(offset_bytes = -1, size_bytes = 20 * 1024)
        self._l1_address_map["trisc1"] = tt_device.BinarySlot(offset_bytes = -1, size_bytes = 16 * 1024)
        self._l1_address_map["trisc2"] = tt_device.BinarySlot(offset_bytes = -1, size_bytes = 20 * 1024)
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
    SIG_SEL_CONST = 5 # TODO (#75): Unknown constant!!!!

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

    # TODO (#90): Harvesting is different in blackhole. Both x and y can be harvested... For now, just an identity mapping
    def _handle_harvesting_for_nocTr_noc0_map(self, num_harvested_rows):
        self.nocTr_x_to_noc0_x = {i: i for i in range(0, self.row_count())}

    def __init__(self, id, arch, cluster_desc, device_desc_path, context):
        super().__init__(id, arch, cluster_desc, {"functional_workers": BlackholeL1AddressMap(), "eth": BlackholeEthL1AddressMap(), "dram": BlackholeDRAMEpochCommandAddressMap()}, device_desc_path, context)

    def no_tensix_row_count(self):
        return 2

    def no_tensix_col_count(self):
        return 2

    def get_num_msgs_received(self, loc, stream_id):
        return int(self.get_stream_reg_field(loc, stream_id, 224 + 5, 0, 24))

    def get_curr_phase_num_msgs_remaining(self, loc, stream_id):
        return int(self.get_stream_reg_field(loc, stream_id, 36, 12, 12))

    def get_remote_source(self, loc, stream_id):
        return self.get_stream_reg_field(loc, stream_id, 10, 5, 1)

    def get_remote_receiver(self, loc, stream_id):
        return self.get_stream_reg_field(loc, stream_id, 10, 8, 1)

    # Populates a dict with register names and current values on core x-y for stream with id 'stream_id'
    def read_stream_regs_direct(self, loc, stream_id):
        reg = {}
        reg["STREAM_ID"] = self.get_stream_reg_field(loc, stream_id, 224 + 5, 24, 6)
        reg["PHASE_AUTO_CFG_PTR (word addr)"] = self.get_stream_reg_field(
            loc, stream_id, 12, 0, 24
        )
        reg["CURR_PHASE"] = self.get_stream_reg_field(loc, stream_id, 11, 0, 20)

        reg["CURR_PHASE_NUM_MSGS_REMAINING"] = self.get_stream_reg_field(
            loc, stream_id, 36, 12, 12
        )
        reg["NUM_MSGS_RECEIVED"] = self.get_stream_reg_field(
            loc, stream_id, 224 + 5, 0, 24
        )
        reg["NEXT_MSG_ADDR"] = self.get_stream_reg_field(loc, stream_id, 224 + 6, 0, 32)
        reg["NEXT_MSG_SIZE"] = self.get_stream_reg_field(loc, stream_id, 224 + 7, 0, 32)
        reg["OUTGOING_DATA_NOC"] = self.get_stream_reg_field(loc, stream_id, 10, 1, 1)
        local_sources_connected = self.get_stream_reg_field(loc, stream_id, 10, 3, 1)
        reg["LOCAL_SOURCES_CONNECTED"] = local_sources_connected
        reg["SOURCE_ENDPOINT"] = self.get_stream_reg_field(loc, stream_id, 10, 4, 1)
        remote_source = self.get_stream_reg_field(loc, stream_id, 10, 5, 1)
        reg["REMOTE_SOURCE"] = remote_source
        reg["RECEIVER_ENDPOINT"] = self.get_stream_reg_field(loc, stream_id, 10, 6, 1)
        reg["LOCAL_RECEIVER"] = self.get_stream_reg_field(loc, stream_id, 10, 7, 1)
        remote_receiver = self.get_stream_reg_field(loc, stream_id, 10, 8, 1)
        reg["REMOTE_RECEIVER"] = remote_receiver
        reg["NEXT_PHASE_SRC_CHANGE"] = self.get_stream_reg_field(
            loc, stream_id, 10, 12, 1
        )
        reg["NEXT_PHASE_DST_CHANGE"] = self.get_stream_reg_field(
            loc, stream_id, 10, 13, 1
        )

        if remote_source == 1:
            reg["INCOMING_DATA_NOC"] = self.get_stream_reg_field(
                loc, stream_id, 10, 0, 1
            )
            reg["REMOTE_SRC_X"] = self.get_stream_reg_field(loc, stream_id, 0, 0, 6)
            reg["REMOTE_SRC_Y"] = self.get_stream_reg_field(loc, stream_id, 0, 6, 6)
            reg["REMOTE_SRC_STREAM_ID"] = self.get_stream_reg_field(
                loc, stream_id, 0, 12, 6
            )
            reg["REMOTE_SRC_UPDATE_NOC"] = self.get_stream_reg_field(
                loc, stream_id, 10, 2, 1
            )
            reg["REMOTE_SRC_PHASE"] = self.get_stream_reg_field(
                loc, stream_id, 1, 0, 20
            )
            reg["REMOTE_SRC_DEST_INDEX"] = self.get_stream_reg_field(
                loc, stream_id, 0, 18, 6
            )
            reg["REMOTE_SRC_IS_MCAST"] = self.get_stream_reg_field(
                loc, stream_id, 10, 16, 1
            )

        if remote_receiver == 1:
            reg["OUTGOING_DATA_NOC"] = self.get_stream_reg_field(
                loc, stream_id, 10, 1, 1
            )
            reg["REMOTE_DEST_STREAM_ID"] = self.get_stream_reg_field(
                loc, stream_id, 2, 12, 6
            )
            reg["REMOTE_DEST_X"] = self.get_stream_reg_field(loc, stream_id, 2, 0, 6)
            reg["REMOTE_DEST_Y"] = self.get_stream_reg_field(loc, stream_id, 2, 6, 6)
            reg["REMOTE_DEST_BUF_START"] = self.get_stream_reg_field(
                loc, stream_id, 3, 0, 16
            )
            reg["REMOTE_DEST_BUF_SIZE"] = self.get_stream_reg_field(
                loc, stream_id, 4, 0, 16
            )
            reg["REMOTE_DEST_BUF_WR_PTR"] = self.get_stream_reg_field(
                loc, stream_id, 5, 0, 16
            )
            reg["REMOTE_DEST_MSG_INFO_WR_PTR"] = self.get_stream_reg_field(
                loc, stream_id, 9, 0, 16
            )
            reg["DEST_DATA_BUF_NO_FLOW_CTRL"] = self.get_stream_reg_field(
                loc, stream_id, 10, 15, 1
            )
            mcast_en = self.get_stream_reg_field(loc, stream_id, 13, 12, 1)
            reg["MCAST_EN"] = mcast_en
            if mcast_en == 1:
                reg["MCAST_END_X"] = self.get_stream_reg_field(loc, stream_id, 13, 0, 6)
                reg["MCAST_END_Y"] = self.get_stream_reg_field(loc, stream_id, 13, 6, 6)
                reg["MCAST_LINKED"] = self.get_stream_reg_field(
                    loc, stream_id, 13, 13, 1
                )
                reg["MCAST_VC"] = self.get_stream_reg_field(loc, stream_id, 13, 14, 1)
                reg["MCAST_DEST_NUM"] = self.get_stream_reg_field(
                    loc, stream_id, 14, 0, 16
                )
                for i in range(0, 31):
                    reg["DEST_BUF_SPACE_AVAILABLE[{i:d}]"] = self.get_stream_reg_field(
                        loc, stream_id, 64 + i, 0, 32
                    )
            else:
                reg["DEST_BUF_SPACE_AVAILABLE[0]"] = self.get_stream_reg_field(
                    loc, stream_id, 64, 0, 32
                )

        if local_sources_connected == 1:
            local_src_mask_lo = self.get_stream_reg_field(loc, stream_id, 48, 0, 32)
            local_src_mask_hi = self.get_stream_reg_field(loc, stream_id, 49, 0, 32)
            local_src_mask = (local_src_mask_hi << 32) | local_src_mask_lo
            reg["LOCAL_SRC_MASK"] = local_src_mask
            reg["MSG_ARB_GROUP_SIZE"] = self.get_stream_reg_field(
                loc, stream_id, 15, 0, 3
            )
            reg["MSG_SRC_IN_ORDER_FWD"] = self.get_stream_reg_field(
                loc, stream_id, 15, 3, 1
            )
            reg["STREAM_MSG_SRC_IN_ORDER_FWD_NUM_MSREG_INDEX"] = (
                self.get_stream_reg_field(loc, stream_id, 16, 0, 24)
            )
        else:
            reg["BUF_START (word addr)"] = self.get_stream_reg_field(
                loc, stream_id, 6, 0, 16
            )
            reg["BUF_SIZE (words)"] = self.get_stream_reg_field(
                loc, stream_id, 7, 0, 16
            )
            reg["BUF_RD_PTR (word addr)"] = self.get_stream_reg_field(
                loc, stream_id, 24, 0, 16
            )
            reg["BUF_WR_PTR (word addr)"] = self.get_stream_reg_field(
                loc, stream_id, 25, 0, 16
            )
            reg["MSG_INFO_PTR (word addr)"] = self.get_stream_reg_field(
                loc, stream_id, 8, 0, 16
            )
            reg["MSG_INFO_WR_PTR (word addr)"] = self.get_stream_reg_field(
                loc, stream_id, 26, 0, 16
            )
            reg["STREAM_BUF_SPACE_AVAILABLE_REG_INDEX (word addr)"] = (
                self.get_stream_reg_field(loc, stream_id, 28, 0, 16)
            )
            reg["DATA_BUF_NO_FLOW_CTRL"] = self.get_stream_reg_field(
                loc, stream_id, 10, 14, 1
            )
            reg["UNICAST_VC_REG"] = self.get_stream_reg_field(loc, stream_id, 10, 18, 3)
            reg["REG_UPDATE_VC_REG"] = self.get_stream_reg_field(
                loc, stream_id, 10, 21, 3
            )

        reg["SCRATCH_REG0"] = self.get_stream_reg_field(loc, stream_id, 248, 0, 32)
        reg["SCRATCH_REG1"] = self.get_stream_reg_field(loc, stream_id, 249, 0, 32)
        reg["SCRATCH_REG2"] = self.get_stream_reg_field(loc, stream_id, 250, 0, 32)
        reg["SCRATCH_REG3"] = self.get_stream_reg_field(loc, stream_id, 251, 0, 32)
        reg["SCRATCH_REG4"] = self.get_stream_reg_field(loc, stream_id, 252, 0, 32)
        reg["SCRATCH_REG5"] = self.get_stream_reg_field(loc, stream_id, 253, 0, 32)
        for i in range(0, 10):
            reg[f"DEBUG_STATUS[{i:d}]"] = self.get_stream_reg_field(
                loc, stream_id, 224 + i, 0, 32
            )
            if i == 8:
                phase_state = self.get_stream_reg_field(loc, stream_id, 224 + i, 0, 4)
                src_ready_state = self.get_stream_reg_field(
                    loc, stream_id, 224 + i, 4, 3
                )
                dest_ready_state = self.get_stream_reg_field(
                    loc, stream_id, 224 + i, 7, 3
                )
                src_side_phase_complete = self.get_stream_reg_field(
                    loc, stream_id, 224 + i, 10, 1
                )
                dest_side_phase_complete = self.get_stream_reg_field(
                    loc, stream_id, 224 + i, 11, 1
                )
                src_state = self.get_stream_reg_field(loc, stream_id, 224 + i, 16, 4)
                dest_state = self.get_stream_reg_field(loc, stream_id, 224 + i, 20, 3)
                # IMPROVE: add back the interpretation in get_as_str
                reg["PHASE_STATE"] = phase_state
                reg["SRC_READY_STATE"] = src_ready_state
                reg["DEST_READY_STATE"] = dest_ready_state
                reg["SRC_SIDE_PHASE_COMPLETE"] = src_side_phase_complete
                reg["DEST_SIDE_PHASE_COMPLETE"] = dest_side_phase_complete
                reg["SRC_STATE"] = src_state
                reg["DEST_STATE"] = dest_state

        return reg

    # This is from device/bin/silicon/<device>/ttx_status.py
    def get_endpoint_type(self, x, y):
        if x == 0:
            if y == 3:
                return "PCIE"
            elif y == 10:
                return "ARC"
            elif y in [2, 9, 4, 8]:
                return "Padding"
            else:
                return "GDDR"
        elif x == 5:
            return "GDDR"
        elif y in [0, 6]:
            return "Ethernet"
        else:
            return "Tensix"

    def read_print_noc_reg(
        self, loc, noc_id, reg_name, reg_index, reg_type=tt_device.Device.RegType.Status
    ):
        if reg_type == tt_device.Device.RegType.Cmd:
            status_offset = 0
        elif reg_type == tt_device.Device.RegType.Config:
            status_offset = 0x100
        else:
            status_offset = 0x200
        (x, y) = loc.to("nocVirt")
        endpoint_type = self.get_endpoint_type(x, y)
        if endpoint_type in ["Ethernet", "Tensix"]:
            reg_addr = 0xFFB20000 + (noc_id * 0x10000) + status_offset + (reg_index * 4)
            val = read_word_from_device(OnChipCoordinate(x, y, "nocVirt", 0), reg_addr, 0, self._context)
        elif endpoint_type in ["GDDR", "PCIE", "ARC"]:
            reg_addr = 0xFFFB20000 + status_offset + (reg_index * 4)
            xr = x if noc_id == 0 else 9 - x
            yr = y if noc_id == 0 else 11 - y
            val = read_word_from_device(OnChipCoordinate(xr, yr, "nocVirt", noc_id), reg_addr, noc_id, self._context)
        elif endpoint_type in ["Padding"]:
            reg_addr = 0xFFB20000 + status_offset + (reg_index * 4)
            xr = x if noc_id == 0 else 9 - x
            yr = y if noc_id == 0 else 11 - y
            val = read_word_from_device(OnChipCoordinate(xr, yr, "nocVirt", noc_id), reg_addr, noc_id, self._context)
        else:
            util.ERROR(f"Unknown endpoint type {endpoint_type}")
        print(
            f"{endpoint_type} x={x:02d},y={y:02d} => NOC{noc_id:d} {reg_name:s} (0x{reg_addr:09x}) = 0x{val:08x} ({val:d})"
        )
        return val

    def get_tensix_configuration_register_base(self) -> int:
        return 0xFFEF0000

    __configuration_register_map = {
        'DISABLE_RISC_BP_Disable_main': tt_device.TensixRegisterDescription(address=2 * 4, mask=0x400000, shift=22),
        'DISABLE_RISC_BP_Disable_trisc': tt_device.TensixRegisterDescription(address=2 * 4, mask=0x3800000, shift=23),
        'DISABLE_RISC_BP_Disable_ncrisc': tt_device.TensixRegisterDescription(address=2 * 4, mask=0x4000000, shift=26),
        'RISCV_IC_INVALIDATE_InvalidateAll': tt_device.TensixRegisterDescription(address=185 * 4, mask=0x1f, shift=0),
    }

    def get_configuration_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in BlackholeDevice.__configuration_register_map:
            return BlackholeDevice.__configuration_register_map[register_name]
        return None

    def get_tenxis_debug_register_base(self) -> int:
        return 0xFFB12000

    __debug_register_map = {
        'RISCV_DEBUG_REG_RISC_DBG_CNTL_0': tt_device.TensixRegisterDescription(address=0x80, mask=0xffffffff, shift=0),
        'RISCV_DEBUG_REG_RISC_DBG_CNTL_1': tt_device.TensixRegisterDescription(address=0x84, mask=0xffffffff, shift=0),
        'RISCV_DEBUG_REG_RISC_DBG_STATUS_0': tt_device.TensixRegisterDescription(address=0x88, mask=0xffffffff, shift=0),
        'RISCV_DEBUG_REG_RISC_DBG_STATUS_1': tt_device.TensixRegisterDescription(address=0x8c, mask=0xffffffff, shift=0),
        'RISCV_DEBUG_REG_SOFT_RESET_0': tt_device.TensixRegisterDescription(address=0x1b0, mask=0xffffffff, shift=0),
        'TRISC_RESET_PC_SEC0_PC': tt_device.TensixRegisterDescription(address=0x228, mask=0xffffffff, shift=0), # Old name from configuration register
        'RISCV_DEBUG_REG_TRISC0_RESET_PC': tt_device.TensixRegisterDescription(address=0x228, mask=0xffffffff, shift=0), # New name
        'TRISC_RESET_PC_SEC1_PC': tt_device.TensixRegisterDescription(address=0x22c, mask=0xffffffff, shift=0), # Old name from configuration register
        'RISCV_DEBUG_REG_TRISC1_RESET_PC': tt_device.TensixRegisterDescription(address=0x22c, mask=0xffffffff, shift=0), # New name
        'TRISC_RESET_PC_SEC2_PC': tt_device.TensixRegisterDescription(address=0x230, mask=0xffffffff, shift=0), # Old name from configuration register
        'RISCV_DEBUG_REG_TRISC2_RESET_PC': tt_device.TensixRegisterDescription(address=0x230, mask=0xffffffff, shift=0), # New name
        'TRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en': tt_device.TensixRegisterDescription(address=0x234, mask=0x7, shift=0), # Old name from configuration register
        'RISCV_DEBUG_REG_TRISC_RESET_PC_OVERRIDE': tt_device.TensixRegisterDescription(address=0x234, mask=0x7, shift=0), # New name
        'NCRISC_RESET_PC_PC': tt_device.TensixRegisterDescription(address=0x238, mask=0xffffffff, shift=0), # Old name from configuration register
        'RISCV_DEBUG_REG_NCRISC_RESET_PC': tt_device.TensixRegisterDescription(address=0x238, mask=0xffffffff, shift=0), # New name
        'NCRISC_RESET_PC_OVERRIDE_Reset_PC_Override_en': tt_device.TensixRegisterDescription(address=0x23c, mask=0x1, shift=0), # Old name from configuration register
        'RISCV_DEBUG_REG_NCRISC_RESET_PC_OVERRIDE': tt_device.TensixRegisterDescription(address=0x23c, mask=0x1, shift=0), # New name
    }

    def get_debug_register_description(self, register_name: str) -> tt_device.TensixRegisterDescription:
        if register_name in BlackholeDevice.__debug_register_map:
            return BlackholeDevice.__debug_register_map[register_name]
        return None
