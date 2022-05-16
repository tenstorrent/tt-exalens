import tt_util as util, os
import tt_device, tt_netlist, tt_stream

# FIX: Move this to chip.py in t6py
CHANNEL_TO_DRAM_LOC = [(1, 0), (1, 6), (4, 0), (4, 6), (7, 0), (7, 6), (10, 0), (10, 6)]

PHYS_X_TO_NOC_0_X = [ 0, 12, 1, 11, 2, 10, 3, 9, 4, 8, 5, 7, 6 ]
PHYS_Y_TO_NOC_0_Y = [ 0, 11, 1, 10, 2, 9,  3, 8, 4, 7, 5, 6 ]
PHYS_X_TO_NOC_1_X = [ 12, 0, 11, 1, 10, 2, 9, 3, 8, 4, 7, 5, 6 ]
PHYS_Y_TO_NOC_1_Y = [ 11, 0, 10, 1, 9,  2, 8, 3, 7, 4, 6, 5 ]
NOC_0_X_TO_PHYS_X = util.reverse_mapping_list (PHYS_X_TO_NOC_0_X)
NOC_0_Y_TO_PHYS_Y = util.reverse_mapping_list (PHYS_Y_TO_NOC_0_Y)
NOC_1_X_TO_PHYS_X = util.reverse_mapping_list (PHYS_X_TO_NOC_1_X)
NOC_1_Y_TO_PHYS_Y = util.reverse_mapping_list (PHYS_Y_TO_NOC_1_Y)

# Coordinate conversion functions 
def physical_to_noc (phys_x, phys_y, noc_id=0):
    if noc_id == 0:
        return (PHYS_X_TO_NOC_0_X[phys_x], PHYS_Y_TO_NOC_0_Y[phys_y])
    else:
        return (PHYS_X_TO_NOC_1_X[phys_x], PHYS_Y_TO_NOC_1_Y[phys_y])

def noc_to_physical (noc_x, noc_y, noc_id=0):
    if noc_id == 0:
        return (NOC_0_X_TO_PHYS_X[noc_x], NOC_0_Y_TO_PHYS_Y[noc_y])
    else:
        return (NOC_1_X_TO_PHYS_X[noc_x], NOC_1_Y_TO_PHYS_Y[noc_y])

def noc0_to_noc1 (noc_x, noc_y):
    phys_x, phys_y = noc_to_physical (noc_x, noc_y, noc_id=0)
    return physical_to_noc (phys_x, phys_y, noc_id=1)

def noc1_to_noc0 (noc_x, noc_y):
    #print (f"noc_x = {noc_x}  noc_y = {noc_y}")
    phys_x, phys_y = noc_to_physical (noc_x, noc_y, noc_id=1)
    return physical_to_noc (phys_x, phys_y, noc_id=0)

# FIX: Check if this is correct
def noc0_to_rc (noc0_x, noc0_y):
    row = noc0_y - 1
    col = noc0_x - 1
    return row, col

def rc_to_noc0 (row, col):
    noc0_y = row + 1
    noc0_x = col + 1
    return noc0_x, noc0_y

# Returns a stream type based on KERNEL_OPERAND_MAPPING_SCHEME
def stream_type (stream_id):
    # From src/firmware/riscv/grayskull/stream_io_map.h
    # Kernel operand mapping scheme:
    KERNEL_OPERAND_MAPPING_SCHEME = [
        { "id_min" : 0,  "id_max" : 7,  "stream_id_min" : 8, "short" : "input", "long" : "(inputs, unpacker-only) => streams 8-15" },
        { "id_min" : 8,  "id_max" : 15, "stream_id_min" : 16, "short" : "param", "long" : "(params, unpacker-only) => streams 16-23" },
        { "id_min" : 16, "id_max" : 23, "stream_id_min" : 24, "short" : "output", "long" : "(outputs, packer-only) => streams 24-31" },
        { "id_min" : 24, "id_max" : 31, "stream_id_min" : 32, "short" : "intermediate", "long" : "(intermediates, packer/unpacker) => streams 32-39" },
        { "id_min" : 32, "id_max" : 63, "stream_id_min" : 32, "short" : "op-relay", "long" : "(operand relay?) => streams 40-63" }, # CHECK THIS
    ]
    for ko in KERNEL_OPERAND_MAPPING_SCHEME:
        s_id_min = ko["stream_id_min"]
        s_id_count = ko["id_max"] - ko["id_min"]
        if stream_id >= s_id_min and stream_id < s_id_min + s_id_count:
            return ko
    util.WARN ("no desc for stream_id=%s" % stream_id)
    return "-"

# Populates a dict with register names and current values on core x-y for stream with id 'stream_id'
def read_stream_regs(chip, x, y, stream_id):
    reg = {}
    reg["STREAM_ID"] =                                            get_stream_reg_field(chip, x, y, stream_id, 224+9, 0, 6)
    reg["PHASE_AUTO_CFG_PTR (word addr)"] =                       get_stream_reg_field(chip, x, y, stream_id, 12, 0, 24)
    reg["CURR_PHASE"] =                                           get_stream_reg_field(chip, x, y, stream_id, 11, 0, 20)
    reg["CURR_PHASE_NUM_MSGS_REMAINING"] =                        get_stream_reg_field(chip, x, y, stream_id, 35, 0, 12)
    reg["NUM_MSGS_RECEIVED"] =                                    get_stream_reg_field(chip, x, y, stream_id, 224+5, 0, 16)
    reg["NEXT_MSG_ADDR"] =                                        get_stream_reg_field(chip, x, y, stream_id, 224+6, 0, 16)
    reg["NEXT_MSG_SIZE"] =                                        get_stream_reg_field(chip, x, y, stream_id, 224+6, 16, 16)
    reg["OUTGOING_DATA_NOC"] =                                    get_stream_reg_field(chip, x, y, stream_id, 10, 1, 1)
    local_sources_connected =                                     get_stream_reg_field(chip, x, y, stream_id, 10, 3, 1)
    reg["LOCAL_SOURCES_CONNECTED"] =                              local_sources_connected
    reg["SOURCE_ENDPOINT"] =                                      get_stream_reg_field(chip, x, y, stream_id, 10, 4, 1)
    remote_source =                                               get_stream_reg_field(chip, x, y, stream_id, 10, 5, 1)
    reg["REMOTE_SOURCE"] =                                        remote_source
    reg["RECEIVER_ENDPOINT"] =                                    get_stream_reg_field(chip, x, y, stream_id, 10, 6, 1)
    reg["LOCAL_RECEIVER"] =                                       get_stream_reg_field(chip, x, y, stream_id, 10, 7, 1)
    remote_receiver =                                             get_stream_reg_field(chip, x, y, stream_id, 10, 8, 1)
    reg["REMOTE_RECEIVER"] =                                      remote_receiver
    reg["NEXT_PHASE_SRC_CHANGE"] =                                get_stream_reg_field(chip, x, y, stream_id, 10, 12, 1)
    reg["NEXT_PHASE_DST_CHANGE"] =                                get_stream_reg_field(chip, x, y, stream_id, 10, 13, 1)

    if remote_source == 1:
        reg["INCOMING_DATA_NOC"] =                                get_stream_reg_field(chip, x, y, stream_id, 10, 0, 1)
        reg["REMOTE_SRC_X"] =                                     get_stream_reg_field(chip, x, y, stream_id, 0, 0, 6)
        reg["REMOTE_SRC_Y"] =                                     get_stream_reg_field(chip, x, y, stream_id, 0, 6, 6)
        reg["REMOTE_SRC_STREAM_ID"] =                             get_stream_reg_field(chip, x, y, stream_id, 0, 12, 6)
        reg["REMOTE_SRC_UPDATE_NOC"] =                            get_stream_reg_field(chip, x, y, stream_id, 10, 2, 1)
        reg["REMOTE_SRC_PHASE"] =                                 get_stream_reg_field(chip, x, y, stream_id, 1, 0, 20)
        reg["REMOTE_SRC_DEST_INDEX"] =                            get_stream_reg_field(chip, x, y, stream_id, 0, 18, 6)
        reg["REMOTE_SRC_IS_MCAST"] =                              get_stream_reg_field(chip, x, y, stream_id, 10, 16, 1)

    if remote_receiver == 1:
        reg["OUTGOING_DATA_NOC"] =                                get_stream_reg_field(chip, x, y, stream_id, 10, 1, 1)
        reg["REMOTE_DEST_STREAM_ID"] =                            get_stream_reg_field(chip, x, y, stream_id, 2, 12, 6)
        reg["REMOTE_DEST_X"] =                                    get_stream_reg_field(chip, x, y, stream_id, 2, 0, 6)
        reg["REMOTE_DEST_Y"] =                                    get_stream_reg_field(chip, x, y, stream_id, 2, 6, 6)
        reg["REMOTE_DEST_BUF_START"] =                            get_stream_reg_field(chip, x, y, stream_id, 3, 0, 16)
        reg["REMOTE_DEST_BUF_SIZE"] =                             get_stream_reg_field(chip, x, y, stream_id, 4, 0, 16)
        reg["REMOTE_DEST_BUF_WR_PTR"] =                           get_stream_reg_field(chip, x, y, stream_id, 5, 0, 16)
        reg["REMOTE_DEST_MSG_INFO_WR_PTR"] =                      get_stream_reg_field(chip, x, y, stream_id, 9, 0, 16)
        reg["DEST_DATA_BUF_NO_FLOW_CTRL"] =                       get_stream_reg_field(chip, x, y, stream_id, 10, 15, 1)
        mcast_en =                                                get_stream_reg_field(chip, x, y, stream_id, 13, 12, 1)
        reg["MCAST_EN"] =                                         mcast_en
        if mcast_en == 1:
            reg["MCAST_END_X"] =                                  get_stream_reg_field(chip, x, y, stream_id, 13, 0, 6)
            reg["MCAST_END_Y"] =                                  get_stream_reg_field(chip, x, y, stream_id, 13, 6, 6)
            reg["MCAST_LINKED"] =                                 get_stream_reg_field(chip, x, y, stream_id, 13, 13, 1)
            reg["MCAST_VC"] =                                     get_stream_reg_field(chip, x, y, stream_id, 13, 14, 1)
            reg["MCAST_DEST_NUM"] =                               get_stream_reg_field(chip, x, y, stream_id, 15, 0, 16)

    if local_sources_connected == 1:
        local_src_mask_lo =                                       get_stream_reg_field(chip, x, y, stream_id, 48, 0, 32)
        local_src_mask_hi =                                       get_stream_reg_field(chip, x, y, stream_id, 49, 0, 32)
        local_src_mask =                                          (local_src_mask_hi << 32) | local_src_mask_lo
        reg["LOCAL_SRC_MASK"] =                                   local_src_mask
        reg["MSG_ARB_GROUP_SIZE"] =                               get_stream_reg_field(chip, x, y, stream_id, 13, 16, 3)
        reg["MSG_SRC_IN_ORDER_FWD"] =                             get_stream_reg_field(chip, x, y, stream_id, 13, 19, 1)
        reg["STREAM_MSG_SRC_IN_ORDER_FWD_NUM_MSREG_INDEX"] =   get_stream_reg_field(chip, x, y, stream_id, 14, 0, 24)
    else:
        reg["BUF_START (word addr)"] =                            get_stream_reg_field(chip, x, y, stream_id, 6, 0, 16)
        reg["BUF_SIZE (words)"] =                                 get_stream_reg_field(chip, x, y, stream_id, 7, 0, 16)
        reg["BUF_RD_PTR (word addr)"] =                           get_stream_reg_field(chip, x, y, stream_id, 23, 0, 16)
        reg["BUF_WR_PTR (word addr)"] =                           get_stream_reg_field(chip, x, y, stream_id, 24, 0, 16)
        reg["MSG_INFO_PTR (word addr)"] =                         get_stream_reg_field(chip, x, y, stream_id, 8, 0, 16)
        reg["MSG_INFO_WR_PTR (word addr)"] =                      get_stream_reg_field(chip, x, y, stream_id, 25, 0, 16)
        reg["STREAM_BUF_SPACE_AVAILABLE_REG_INDEX (word addr)"] = get_stream_reg_field(chip, x, y, stream_id, 27, 0, 16)
        reg["DATA_BUF_NO_FLOW_CTRL"] =                            get_stream_reg_field(chip, x, y, stream_id, 10, 14, 1)
        reg["UNICAST_VC_REG"] =                                   get_stream_reg_field(chip, x, y, stream_id, 10, 18, 3)
        reg["REG_UPDATE_VC_REG"] =                                get_stream_reg_field(chip, x, y, stream_id, 10, 21, 3)

    reg["SCRATCH_REG0"] =                                         get_stream_reg_field(chip, x, y, stream_id, 248, 0, 32)
    reg["SCRATCH_REG1"] =                                         get_stream_reg_field(chip, x, y, stream_id, 249, 0, 32)
    reg["SCRATCH_REG2"] =                                         get_stream_reg_field(chip, x, y, stream_id, 250, 0, 32)
    reg["SCRATCH_REG3"] =                                         get_stream_reg_field(chip, x, y, stream_id, 251, 0, 32)
    reg["SCRATCH_REG4"] =                                         get_stream_reg_field(chip, x, y, stream_id, 252, 0, 32)
    reg["SCRATCH_REG5"] =                                         get_stream_reg_field(chip, x, y, stream_id, 253, 0, 32)
    for i in range(0, 10):
        reg[f"DEBUG_STATUS[{i:d}]"] =                             get_stream_reg_field(chip, x, y, stream_id, 224+i, 0, 32)

    return reg

# Function to print a full dump of a location x-y
def full_dump_xy(chip_id, x, y):
    for stream_id in range (0, 64):
        print()
        stream = read_stream_regs(chip_id, x, y, stream_id)
        for reg, value in tt_stream.items():
            print(f"Tensix x={x:02d},y={y:02d} => stream {stream_id:02d} {reg} = {value}")

    for noc_id in range (0, 2):
        print()
        read_print_noc_reg(chip_id, x, y, noc_id, "nonposted write reqs sent", 0xA)
        read_print_noc_reg(chip_id, x, y, noc_id, "posted write reqs sent", 0xB)
        read_print_noc_reg(chip_id, x, y, noc_id, "nonposted write words sent", 0x8)
        read_print_noc_reg(chip_id, x, y, noc_id, "posted write words sent", 0x9)
        read_print_noc_reg(chip_id, x, y, noc_id, "write acks received", 0x1)
        read_print_noc_reg(chip_id, x, y, noc_id, "read reqs sent", 0x5)
        read_print_noc_reg(chip_id, x, y, noc_id, "read words received", 0x3)
        read_print_noc_reg(chip_id, x, y, noc_id, "read resps received", 0x2)
        print()
        read_print_noc_reg(chip_id, x, y, noc_id, "nonposted write reqs received", 0x1A)
        read_print_noc_reg(chip_id, x, y, noc_id, "posted write reqs received", 0x1B)
        read_print_noc_reg(chip_id, x, y, noc_id, "nonposted write words received", 0x18)
        read_print_noc_reg(chip_id, x, y, noc_id, "posted write words received", 0x19)
        read_print_noc_reg(chip_id, x, y, noc_id, "write acks sent", 0x10)
        read_print_noc_reg(chip_id, x, y, noc_id, "read reqs received", 0x15)
        read_print_noc_reg(chip_id, x, y, noc_id, "read words sent", 0x13)
        read_print_noc_reg(chip_id, x, y, noc_id, "read resps sent", 0x12)
        print()
        read_print_noc_reg(chip_id, x, y, noc_id, "router port x out vc full credit out vc stall", 0x24)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port y out vc full credit out vc stall", 0x22)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port niu out vc full credit out vc stall", 0x20)
        print()
        read_print_noc_reg(chip_id, x, y, noc_id, "router port x VC14 & VC15 dbg", 0x3d)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port x VC12 & VC13 dbg", 0x3c)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port x VC10 & VC11 dbg", 0x3b)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port x VC8 & VC9 dbg", 0x3a)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port x VC6 & VC7 dbg", 0x39)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port x VC4 & VC5 dbg", 0x38)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port x VC2 & VC3 dbg", 0x37)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port x VC0 & VC1 dbg", 0x36)
        print()
        read_print_noc_reg(chip_id, x, y, noc_id, "router port y VC14 & VC15 dbg", 0x35)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port y VC12 & VC13 dbg", 0x34)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port y VC10 & VC11 dbg", 0x33)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port y VC8 & VC9 dbg", 0x32)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port y VC6 & VC7 dbg", 0x31)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port y VC4 & VC5 dbg", 0x30)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port y VC2 & VC3 dbg", 0x2f)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port y VC0 & VC1 dbg", 0x2e)
        print()
        read_print_noc_reg(chip_id, x, y, noc_id, "router port niu VC6 & VC7 dbg", 0x29)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port niu VC4 & VC5 dbg", 0x28)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port niu VC2 & VC3 dbg", 0x27)
        read_print_noc_reg(chip_id, x, y, noc_id, "router port niu VC0 & VC1 dbg", 0x26)

    en = 1
    rd_sel = 0
    pc_mask = 0x7fffffff
    daisy_sel = 7

    sig_sel = 0xff
    rd_sel = 0
    tt_device.pci_write_xy(chip_id, x, y, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
    test_val1 = tt_device.pci_read_xy(chip_id, x, y, 0, 0xffb1205c)
    rd_sel = 1
    tt_device.pci_write_xy(chip_id, x, y, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
    test_val2 = tt_device.pci_read_xy(chip_id, x, y, 0, 0xffb1205c)

    rd_sel = 0
    sig_sel = 2*9
    tt_device.pci_write_xy(chip_id, x, y, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
    brisc_pc = tt_device.pci_read_xy(chip_id, x, y, 0, 0xffb1205c) & pc_mask

    # Doesn't work - looks like a bug for selecting inputs > 31 in daisy stop
    # rd_sel = 0
    # sig_sel = 2*16
    # tt_device.pci_write_xy(chip_id, x, y, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
    # nrisc_pc = tt_device.pci_read_xy(chip_id, x, y, 0, 0xffb1205c) & pc_mask

    rd_sel = 0
    sig_sel = 2*10
    tt_device.pci_write_xy(chip_id, x, y, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
    trisc0_pc = tt_device.pci_read_xy(chip_id, x, y, 0, 0xffb1205c) & pc_mask

    rd_sel = 0
    sig_sel = 2*11
    tt_device.pci_write_xy(chip_id, x, y, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
    trisc1_pc = tt_device.pci_read_xy(chip_id, x, y, 0, 0xffb1205c) & pc_mask

    rd_sel = 0
    sig_sel = 2*12
    tt_device.pci_write_xy(chip_id, x, y, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
    trisc2_pc = tt_device.pci_read_xy(chip_id, x, y, 0, 0xffb1205c) & pc_mask

    # IH: Commented out to reduce chatter
    print()
    print(f"Tensix x={x:02d},y={y:02d} => dbus_test_val1 (expect 7)={test_val1:x}, dbus_test_val2 (expect A5A5A5A5)={test_val2:x}")
    print(f"Tensix x={x:02d},y={y:02d} => brisc_pc=0x{brisc_pc:x}, trisc0_pc=0x{trisc0_pc:x}, trisc1_pc=0x{trisc1_pc:x}, trisc2_pc=0x{trisc2_pc:x}")

    tt_device.pci_write_xy(chip_id, x, y, 0, 0xffb12054, 0)

# Reads and immediately prints a value of a given NOC register
def read_print_noc_reg(chip_id, x, y, noc_id, reg_name, reg_index):
    reg_addr = 0xffb20000 + (noc_id*0x10000) + 0x200 + (reg_index*4)
    val = tt_device.pci_read_xy(chip_id, x, y, 0, reg_addr)
    print(f"Tensix x={x:02d},y={y:02d} => NOC{noc_id:d} {reg_name:s} = 0x{val:08x} ({val:d})")

# Extracts and returns a single field of a stream register
def get_stream_reg_field(chip_id, x, y, stream_id, reg_index, start_bit, num_bits):
    reg_addr = 0xFFB40000 + (stream_id*0x1000) + (reg_index*4)
    val = tt_device.pci_read_xy(chip_id, x, y, 0, reg_addr)
    mask = (1 << num_bits) - 1
    val = (val >> start_bit) & mask
    return val

# Returns whether the stream is configured
def is_stream_configured(stream_data):
    # FIX: Ask Djordje for correct way of doing this 
    return int(stream_data['CURR_PHASE']) > 0 and (int(stream_data['CURR_PHASE_NUM_MSGS_REMAINING']) > 0 or int(stream_data['NUM_MSGS_RECEIVED']))

def is_stream_idle(stream_data):
    return (stream_data["DEBUG_STATUS[7]"] & 0xfff) == 0xc00
def is_stream_active (stream_data):
    return int (stream_data["CURR_PHASE"]) != 0 and int (stream_data["NUM_MSGS_RECEIVED"]) > 0
def is_bad_stream (stream_data):
    return \
        (stream_data["DEBUG_STATUS[1]"] != 0) or \
        (stream_data["DEBUG_STATUS[2]"] & 0x7) == 0x4 or \
        (stream_data["DEBUG_STATUS[2]"] & 0x7) == 0x2
def is_gsync_hung (chip, x, y):
    return tt_device.pci_read_xy(chip, x, y, 0, 0xffb2010c) == 0xB0010000
def is_ncrisc_done (chip, x, y):
    return tt_device.pci_read_xy(chip, x, y, 0, 0xffb2010c) == 0x1FFFFFF1

#
# Device
#
class GrayskullDevice (tt_device.Device):
    def __init__(self):
        # 1. Load the netlist itself
        self.yaml_file = tt_netlist.YamlFile ("device/grayskull_120_arch.yaml")

    def physical_to_noc (self, phys_x, phys_y, noc_id=0): return physical_to_noc(phys_x, phys_y, noc_id=noc_id)
    def noc_to_physical (self, noc_x, noc_y, noc_id=0): return noc_to_physical(noc_x, noc_y, noc_id=noc_id)
    def noc0_to_noc1 (self, noc_x, noc_y): return noc0_to_noc1(noc_x, noc_y)
    def noc1_to_noc0 (self, noc_x, noc_y): return noc1_to_noc0(noc_x, noc_y)
    def noc0_to_rc (self, noc0_x, noc0_y): return noc0_to_rc(noc0_x, noc0_y)
    def rc_to_noc0 (self, row, col): return rc_to_noc0(row, col)
    def stream_type (self, stream_id): return stream_type (stream_id)
    def full_dump_xy(self, x, y): return full_dump_xy(self.id(), x, y)
    def is_stream_idle (self, regs): return is_stream_idle (regs)
    def as_noc_0 (self, x, y, noc_id):
        if noc_id == 0:
            return (x, y)
        else:
            return (self.noc1_to_noc0 (x,y))

    def is_bad_stream(self, regs): return is_bad_stream(regs)
    def is_gsync_hung(self, x, y): return is_gsync_hung(self.id(), x, y)
    def is_ncrisc_done(self, x, y): return is_ncrisc_done(self.id(), x, y)

    def read_stream_regs(self, noc0_loc, stream_id):
        return read_stream_regs (self.id(), noc0_loc[0], noc0_loc[1], stream_id)

    def is_stream_configured (self, stream_regs):
        return is_stream_configured (stream_regs)

    def is_stream_active (self, stream_regs):
        return is_stream_active (stream_regs)

    def stream_epoch (self, stream_regs):
        return int(stream_regs['CURR_PHASE']) >> 10

    def noc_to_physical(self, noc_loc, noc_id=0):
        return noc_to_physical (noc_loc[0], noc_loc[1], noc_id=noc_id)

    def get_stream_phase (self, x, y, stream_id):
        return get_stream_reg_field(self.id(), x, y, stream_id, 11, 0, 20)


