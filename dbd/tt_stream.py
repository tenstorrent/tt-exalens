from dbd.tt_object import TTObject
import tt_util as util, re
import tt_object

# The field names we want to show as hexadecimal numbers
HEX_FIELDS = {
    "buf_addr",
    "PHASE_AUTO_CFG_PTR (word addr)",
    "NEXT_MSG_ADDR",
    "NEXT_MSG_SIZE",
    "LOCAL_SRC_MASK",
    "BUF_START (word addr)",
    "BUF_SIZE (words)",
    "BUF_RD_PTR (word addr)",
    "BUF_WR_PTR (word addr)",
    "MSG_INFO_PTR (word addr)",
    "MSG_INFO_WR_PTR (word addr)",
    "STREAM_BUF_SPACE_AVAILABLE_REG_INDEX (word addr)",
    "dram_buf_noc_addr"
}

# The field names we want to show as 0-padded hexadecimal numbers
HEX0_FIELDS = { f"DEBUG_STATUS[{i:d}]" for i in range (0,10) }.union ({ f"SCRATCH_REG{i}" for i in range (0,6) })

# Converts field value to string (hex or decimal...)
def get_as_str (fld, val):
    if fld in HEX_FIELDS:
        if fld == "dram_buf_noc_addr":
            return f"{(val>>32) & 0x3f}-{(val>>38) & 0x3f} 0x{val&0xffffffff:x}"
        else:
            return (f"0x{val:x}")
    elif fld in HEX0_FIELDS:
        return (f"0x{val:08x}")
    else:
        return f"{val:d}"

# Given a dict returned by tt_device.read_stream_regs, convert to strings (and colorize)
def convert_reg_dict_to_strings(device, regs):
    string_regs = {}
    for k in regs:
        # Convert to strings
        string_regs[k] = get_as_str (k, regs[k])
        # If on noc-1, convert the coords no noc-0 coords
        if "REMOTE_SRC_UPDATE_NOC" in regs and regs["REMOTE_SRC_UPDATE_NOC"] > 0:
            try:
                if k == "REMOTE_SRC_X":
                    noc0_loc = device.noc1_to_noc0 ( ( regs[k], 0 ) )
                    string_regs[k] += f"({util.CLR_INFO}{noc0_loc[0]}{util.CLR_END})"
                if k == "REMOTE_SRC_Y":
                    noc0_loc = device.noc1_to_noc0 ( ( 0, regs[k] ) )
                    string_regs[k] += f"({util.CLR_INFO}{noc0_loc[1]}{util.CLR_END})"
            except:
                print (f"{util.CLR_ERR}Invalid coordinate passed k={k} regs[k]={regs[k]} {util.CLR_END}")
                raise

    return string_regs

# Reads all stream registers for a given device-x-y core
# Converts the readings into a user-friendly strings
# Returns the summary, and suggestions for navigation
# IMPROVE: this function does too much. should be broken up
def get_core_stream_summary (device, noc0_loc):
    all_streams_summary = {}
    navigation_suggestions = [ ]
    for stream_id in range (0, 64):
        val = ""
        # Check if idle
        regs = device.read_stream_regs (noc0_loc, stream_id)
        reg_strings = convert_reg_dict_to_strings(device, regs)
        idle = device.is_stream_idle (regs)

        # Construct the navigation suggestions, and stream idle status
        if regs["REMOTE_SOURCE"] !=0 and 'REMOTE_SRC_X' in regs:
            val += f"RS-{reg_strings['REMOTE_SRC_X']}-{reg_strings['REMOTE_SRC_Y']}-{reg_strings['REMOTE_SRC_STREAM_ID']} "
            noc0_x, noc0_y = device.as_noc_0 ( (regs['REMOTE_SRC_X'], regs['REMOTE_SRC_Y']), regs['REMOTE_SRC_UPDATE_NOC'])
            navigation_suggestions.append (\
                { 'description': 'Go to source',
                  'cmd' : f"s {noc0_x} {noc0_y} {reg_strings['REMOTE_SRC_STREAM_ID']}",
                  'loc' : (noc0_x, noc0_y)
                })
        if regs["REMOTE_RECEIVER"] !=0 and 'REMOTE_DEST_X' in regs:
            val += f"RR-{reg_strings['REMOTE_DEST_X']}-{reg_strings['REMOTE_DEST_Y']}-{reg_strings['REMOTE_DEST_STREAM_ID']} "
            noc0_x, noc0_y = device.as_noc_0 ( (regs['REMOTE_DEST_X'], regs['REMOTE_DEST_Y']), regs['OUTGOING_DATA_NOC'])
            navigation_suggestions.append (\
                { 'description': 'Go to destination',
                  'cmd' : f"s {noc0_x} {noc0_y} {reg_strings['REMOTE_DEST_STREAM_ID']}",
                  'loc' : (noc0_x, noc0_y)
                })
        if regs["LOCAL_SOURCES_CONNECTED"]!=0:
            val += "LSC "

        if not idle:
            all_streams_summary[f"{stream_id}"] = val
        else:
            val += "idle"
    return all_streams_summary, navigation_suggestions

#
# Stream Class
#
# ID (device_id, x, y, stream_id, phase)
class Stream(TTObject):
    # Return (chip_id, noc0_X, noc0_Y, stream_id) given a designator from blob.yaml
    def get_stream_tuple_from_designator (designator):
        # Example full name: chip_0__y_1__x_1__stream_id_8
        vals = re.findall(r'chip_(\d+)__y_(\d+)__x_(\d+)__stream_id_(\d+)', designator)
        # print (f"{designator}, {vals}")
        return ( int(vals[0][0]), int (vals[0][2]), int (vals[0][1]), int (vals[0][3]) )

    def __init__(self, graph, designator, data):
        self.designator = designator
        self._id = Stream.get_stream_tuple_from_designator (designator) + ( data['phase_id'], )
        self.root = data
        self.graph = graph
        self.__buffer_id = self.root.get ("buf_id", None)
        self.__pipe_id = self.root.get ("pipe_id", None)

    # Accessors
    def get_buffer_id (self):
        return self.__buffer_id
    def get_pipe_id (self):
        return self.__pipe_id

    def on_chip_id (self):
        return ( self._id[1], self._id[2], self._id[3], )

    def noc0_XY(self):
        return (self._id[1], self._id[2])

    def stream_id(self):
        return self._id[3]