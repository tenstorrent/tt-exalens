import tt_util as util, os
import tt_device

phase_state_map = {
    0: "PHASE_START",
    1: "PHASE_AUTO_CONFIG",
    2: "PHASE_AUTO_CONFIG_SENT",
    3: "PHASE_ADVANCE_WAIT",
    4: "PHASE_PREV_DATA_FLUSH_WAIT",
    5: "PHASE_FWD_DATA"
    }

dest_state_map = {
    0 : "DEST_IDLE",
    1 : "DEST_REMOTE",
    2 : "DEST_LOCAL_RDY_WAIT",
    3 : "DEST_LOCAL_HS",
    4 : "DEST_LOCAL",
    5 : "DEST_ENDPOINT",
    6 : "DEST_NO_FWD"
    }

dest_ready_state_map = {
    0 : "DEST_READY_IDLE",
    1 : "DEST_READY_SEND_FIRST",
    2 : "DEST_READY_WAIT_DATA",
    3 : "DEST_READY_SEND_SECOND",
    4 : "DEST_READY_FWD_DATA"
    }

src_ready_state_map = {
    0 : "SRC_READY_IDLE",
    1 : "SRC_READY_WAIT_CFG",
    2 : "SRC_READY_DEST_READY_TABLE_RD",
    3 : "SRC_READY_SEND_UPDATE",
    4 : "SRC_READY_WAIT_ALL_DESTS",
    5 : "SRC_READY_FWD_DATA"
    }

src_state_map = {
    0 : "SRC_IDLE",
    1 : "SRC_REMOTE",
    2 : "SRC_LOCAL",
    3 : "SRC_ENDPOINT"
    }

#
# Device
#
class WormholeDevice (tt_device.Device):
    SIG_SEL_CONST = 5
    # # Some of this can be read from architecture yaml file
    DRAM_CHANNEL_TO_NOC0_LOC = [(0, 11), (5, 11), (5, 2), (5, 8), (5, 5), (0, 5)]

    # # Physical location mapping
    PHYS_X_TO_NOC_0_X = [ 0, 9, 1, 8, 2, 7, 3, 6, 4, 5 ]
    PHYS_Y_TO_NOC_0_Y = [ 0, 11, 1, 10, 2, 9,  3, 8, 4, 7, 5, 6 ]
    PHYS_X_TO_NOC_1_X = [ 9, 0, 8, 1, 7, 2, 6, 3, 5, 4 ]
    PHYS_Y_TO_NOC_1_Y = [ 11, 0, 10, 1, 9,  2, 8, 3, 7, 4, 6, 5 ]
    NOC_0_X_TO_PHYS_X = util.reverse_mapping_list (PHYS_X_TO_NOC_0_X)
    NOC_0_Y_TO_PHYS_Y = util.reverse_mapping_list (PHYS_Y_TO_NOC_0_Y)
    NOC_1_X_TO_PHYS_X = util.reverse_mapping_list (PHYS_X_TO_NOC_1_X)
    NOC_1_Y_TO_PHYS_Y = util.reverse_mapping_list (PHYS_Y_TO_NOC_1_Y)

    def noc0_to_rc (self, noc0_loc):
        noc0_x, noc0_y = noc0_loc
        if noc0_x == 0 or noc0_x == 5:
            assert False, "NOC0 x=0 and x=5 do not have an RC coordinate"
        if noc0_y == 0 or noc0_y == 6:
            assert False, "NOC0 y=0 and y=6 do not have an RC coordinate"
        row = noc0_y - 1
        col = noc0_x - 1
        if noc0_x > 5: col-=1
        if noc0_y > 6: row-=1
        return row, col

    def rc_to_noc0 (self, rc_loc):
        row, col = rc_loc
        noc0_y = row + 1
        noc0_x = col + 1
        if noc0_x >= 5: noc0_x+=1
        if noc0_y >= 6: noc0_y+=1
        return noc0_x, noc0_y

    def __init__(self):
        self.yaml_file = util.YamlFile ("device/wormhole_80_arch.yaml")

    def rows_with_no_functional_workers(self): return 2
    def cols_with_no_functional_workers(self): return 2

    # Populates a dict with register names and current values on core x-y for stream with id 'stream_id'
    def read_stream_regs_direct(self, noc0_loc, stream_id):
        reg = {}
        reg["STREAM_ID"] =                                            self.get_stream_reg_field(noc0_loc, stream_id, 224+5, 24, 6)
        reg["PHASE_AUTO_CFG_PTR (word addr)"] =                       self.get_stream_reg_field(noc0_loc, stream_id, 12, 0, 24)
        reg["CURR_PHASE"] =                                           self.get_stream_reg_field(noc0_loc, stream_id, 11, 0, 20)
        reg["CURR_PHASE_NUM_MSGS_REMAINING"] =                        self.get_stream_reg_field(noc0_loc, stream_id, 36, 12, 12)
        reg["NUM_MSGS_RECEIVED"] =                                    self.get_stream_reg_field(noc0_loc, stream_id, 224+5, 0, 24)
        reg["NEXT_MSG_ADDR"] =                                        self.get_stream_reg_field(noc0_loc, stream_id, 224+6, 0, 32)
        reg["NEXT_MSG_SIZE"] =                                        self.get_stream_reg_field(noc0_loc, stream_id, 224+7, 0, 32)
        reg["OUTGOING_DATA_NOC"] =                                    self.get_stream_reg_field(noc0_loc, stream_id, 10, 1, 1)
        local_sources_connected =                                     self.get_stream_reg_field(noc0_loc, stream_id, 10, 3, 1)
        reg["LOCAL_SOURCES_CONNECTED"] =                              local_sources_connected
        reg["SOURCE_ENDPOINT"] =                                      self.get_stream_reg_field(noc0_loc, stream_id, 10, 4, 1)
        remote_source =                                               self.get_stream_reg_field(noc0_loc, stream_id, 10, 5, 1)
        reg["REMOTE_SOURCE"] =                                        remote_source
        reg["RECEIVER_ENDPOINT"] =                                    self.get_stream_reg_field(noc0_loc, stream_id, 10, 6, 1)
        reg["LOCAL_RECEIVER"] =                                       self.get_stream_reg_field(noc0_loc, stream_id, 10, 7, 1)
        remote_receiver =                                             self.get_stream_reg_field(noc0_loc, stream_id, 10, 8, 1)
        reg["REMOTE_RECEIVER"] =                                      remote_receiver
        reg["NEXT_PHASE_SRC_CHANGE"] =                                self.get_stream_reg_field(noc0_loc, stream_id, 10, 12, 1)
        reg["NEXT_PHASE_DST_CHANGE"] =                                self.get_stream_reg_field(noc0_loc, stream_id, 10, 13, 1)

        if remote_source == 1:
            reg["INCOMING_DATA_NOC"] =                                self.get_stream_reg_field(noc0_loc, stream_id, 10, 0, 1)
            reg["REMOTE_SRC_X"] =                                     self.get_stream_reg_field(noc0_loc, stream_id, 0, 0, 6)
            reg["REMOTE_SRC_Y"] =                                     self.get_stream_reg_field(noc0_loc, stream_id, 0, 6, 6)
            reg["REMOTE_SRC_STREAM_ID"] =                             self.get_stream_reg_field(noc0_loc, stream_id, 0, 12, 6)
            reg["REMOTE_SRC_UPDATE_NOC"] =                            self.get_stream_reg_field(noc0_loc, stream_id, 10, 2, 1)
            reg["REMOTE_SRC_PHASE"] =                                 self.get_stream_reg_field(noc0_loc, stream_id, 1, 0, 20)
            reg["REMOTE_SRC_DEST_INDEX"] =                            self.get_stream_reg_field(noc0_loc, stream_id, 0, 18, 6)
            reg["REMOTE_SRC_IS_MCAST"] =                              self.get_stream_reg_field(noc0_loc, stream_id, 10, 16, 1)

        if remote_receiver == 1:
            reg["OUTGOING_DATA_NOC"] =                                self.get_stream_reg_field(noc0_loc, stream_id, 10, 1, 1)
            reg["REMOTE_DEST_STREAM_ID"] =                            self.get_stream_reg_field(noc0_loc, stream_id, 2, 12, 6)
            reg["REMOTE_DEST_X"] =                                    self.get_stream_reg_field(noc0_loc, stream_id, 2, 0, 6)
            reg["REMOTE_DEST_Y"] =                                    self.get_stream_reg_field(noc0_loc, stream_id, 2, 6, 6)
            reg["REMOTE_DEST_BUF_START"] =                            self.get_stream_reg_field(noc0_loc, stream_id, 3, 0, 16)
            reg["REMOTE_DEST_BUF_SIZE"] =                             self.get_stream_reg_field(noc0_loc, stream_id, 4, 0, 16)
            reg["REMOTE_DEST_BUF_WR_PTR"] =                           self.get_stream_reg_field(noc0_loc, stream_id, 5, 0, 16)
            reg["REMOTE_DEST_MSG_INFO_WR_PTR"] =                      self.get_stream_reg_field(noc0_loc, stream_id, 9, 0, 16)
            reg["DEST_DATA_BUF_NO_FLOW_CTRL"] =                       self.get_stream_reg_field(noc0_loc, stream_id, 10, 15, 1)
            mcast_en =                                                self.get_stream_reg_field(noc0_loc, stream_id, 13, 12, 1)
            reg["MCAST_EN"] =                                         mcast_en
            if mcast_en == 1:
                reg["MCAST_END_X"] =                                  self.get_stream_reg_field(noc0_loc, stream_id, 13, 0, 6)
                reg["MCAST_END_Y"] =                                  self.get_stream_reg_field(noc0_loc, stream_id, 13, 6, 6)
                reg["MCAST_LINKED"] =                                 self.get_stream_reg_field(noc0_loc, stream_id, 13, 13, 1)
                reg["MCAST_VC"] =                                     self.get_stream_reg_field(noc0_loc, stream_id, 13, 14, 1)
                reg["MCAST_DEST_NUM"] =                               self.get_stream_reg_field(noc0_loc, stream_id, 14, 0, 16)
                for i in range(0, 31):
                    reg["DEST_BUF_SPACE_AVAILABLE[{i:d}]"] =          self.get_stream_reg_field(noc0_loc, stream_id, 64+i, 0, 32)
            else:
                reg["DEST_BUF_SPACE_AVAILABLE[0]"] =                  self.get_stream_reg_field(noc0_loc, stream_id, 64, 0, 32)

        if local_sources_connected == 1:
            local_src_mask_lo =                                       self.get_stream_reg_field(noc0_loc, stream_id, 48, 0, 32)
            local_src_mask_hi =                                       self.get_stream_reg_field(noc0_loc, stream_id, 49, 0, 32)
            local_src_mask =                                          (local_src_mask_hi << 32) | local_src_mask_lo
            reg["LOCAL_SRC_MASK"] =                                   local_src_mask
            reg["MSG_ARB_GROUP_SIZE"] =                               self.get_stream_reg_field(noc0_loc, stream_id, 15, 0, 3)
            reg["MSG_SRC_IN_ORDER_FWD"] =                             self.get_stream_reg_field(noc0_loc, stream_id, 15, 3, 1)
            reg["STREAM_MSG_SRC_IN_ORDER_FWD_NUM_MSREG_INDEX"] =      self.get_stream_reg_field(noc0_loc, stream_id, 16, 0, 24)
        else:
            reg["BUF_START (word addr)"] =                            self.get_stream_reg_field(noc0_loc, stream_id, 6, 0, 16)
            reg["BUF_SIZE (words)"] =                                 self.get_stream_reg_field(noc0_loc, stream_id, 7, 0, 16)
            reg["BUF_RD_PTR (word addr)"] =                           self.get_stream_reg_field(noc0_loc, stream_id, 24, 0, 16)
            reg["BUF_WR_PTR (word addr)"] =                           self.get_stream_reg_field(noc0_loc, stream_id, 25, 0, 16)
            reg["MSG_INFO_PTR (word addr)"] =                         self.get_stream_reg_field(noc0_loc, stream_id, 8, 0, 16)
            reg["MSG_INFO_WR_PTR (word addr)"] =                      self.get_stream_reg_field(noc0_loc, stream_id, 26, 0, 16)
            reg["STREAM_BUF_SPACE_AVAILABLE_REG_INDEX (word addr)"] = self.get_stream_reg_field(noc0_loc, stream_id, 28, 0, 16)
            reg["DATA_BUF_NO_FLOW_CTRL"] =                            self.get_stream_reg_field(noc0_loc, stream_id, 10, 14, 1)
            reg["UNICAST_VC_REG"] =                                   self.get_stream_reg_field(noc0_loc, stream_id, 10, 18, 3)
            reg["REG_UPDATE_VC_REG"] =                                self.get_stream_reg_field(noc0_loc, stream_id, 10, 21, 3)

        reg["SCRATCH_REG0"] =                                         self.get_stream_reg_field(noc0_loc, stream_id, 248, 0, 32)
        reg["SCRATCH_REG1"] =                                         self.get_stream_reg_field(noc0_loc, stream_id, 249, 0, 32)
        reg["SCRATCH_REG2"] =                                         self.get_stream_reg_field(noc0_loc, stream_id, 250, 0, 32)
        reg["SCRATCH_REG3"] =                                         self.get_stream_reg_field(noc0_loc, stream_id, 251, 0, 32)
        reg["SCRATCH_REG4"] =                                         self.get_stream_reg_field(noc0_loc, stream_id, 252, 0, 32)
        reg["SCRATCH_REG5"] =                                         self.get_stream_reg_field(noc0_loc, stream_id, 253, 0, 32)
        for i in range(0, 10):
            reg[f"DEBUG_STATUS[{i:d}]"] =                             self.get_stream_reg_field(noc0_loc, stream_id, 224+i, 0, 32)
            if i == 8:
                phase_state = self.get_stream_reg_field(noc0_loc, stream_id, 224+i, 0, 4)
                src_ready_state = self.get_stream_reg_field(noc0_loc, stream_id, 224+i, 4, 3)
                dest_ready_state = self.get_stream_reg_field(noc0_loc, stream_id, 224+i, 7, 3)
                src_side_phase_complete = self.get_stream_reg_field(noc0_loc, stream_id, 224+i, 10, 1)
                dest_side_phase_complete = self.get_stream_reg_field(noc0_loc, stream_id, 224+i, 11, 1)
                src_state = self.get_stream_reg_field(noc0_loc, stream_id, 224+i, 16, 4)
                dest_state = self.get_stream_reg_field(noc0_loc, stream_id, 224+i, 20, 3)
                # IMPROVE: add back the interpretation in get_as_str
                reg["PHASE_STATE"] = phase_state
                reg["SRC_READY_STATE"] = src_ready_state
                reg["DEST_READY_STATE"] = dest_ready_state
                reg["SRC_SIDE_PHASE_COMPLETE"] = src_side_phase_complete
                reg["DEST_SIDE_PHASE_COMPLETE"] = dest_side_phase_complete
                reg["SRC_STATE"] = src_state
                reg["DEST_STATE"] = dest_state

        return reg
