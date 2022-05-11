import util, re, os

STREAM_CACHE_FILE_NAME="stream-cache.pkl"

# Returns a summary of non-idle streams within a core
def get_core_stream_summary (chip, x, y):
    all_streams_summary = {}
    navigation_suggestions = [ ]
    for stream_id in range (0, 64):
        val = ""
        # Check if idle
        regs = grayskull.read_stream_regs (chip, x, y, stream_id)
        reg_strings = convert_reg_dict_to_strings(chip, regs, x, y, stream_id)
        idle = is_stream_idle (regs)

        # Construct the navigation suggestions, and stream idle status
        if regs["REMOTE_SOURCE"] !=0 and 'REMOTE_SRC_X' in regs:
            val += f"RS-{reg_strings['REMOTE_SRC_X']}-{reg_strings['REMOTE_SRC_Y']}-{reg_strings['REMOTE_SRC_STREAM_ID']} "
            noc0_x, noc0_y = grayskull.convert_to_noc_0 (regs['REMOTE_SRC_X'], regs['REMOTE_SRC_Y'], regs['REMOTE_SRC_UPDATE_NOC'])
            navigation_suggestions.append (\
                { 'stream_id' : stream_id, 'type' : 'src', "noc0_x" : noc0_x, "noc0_y" : noc0_y, \
                'cmd' : f"s {noc0_x} {noc0_y} {reg_strings['REMOTE_SRC_STREAM_ID']}" })
        if regs["REMOTE_RECEIVER"] !=0 and 'REMOTE_DEST_X' in regs:
            val += f"RR-{reg_strings['REMOTE_DEST_X']}-{reg_strings['REMOTE_DEST_Y']}-{reg_strings['REMOTE_DEST_STREAM_ID']} "
            noc0_x, noc0_y = grayskull.convert_to_noc_0 (regs['REMOTE_DEST_X'], regs['REMOTE_DEST_Y'], regs['OUTGOING_DATA_NOC'])
            navigation_suggestions.append (\
                { 'stream_id' : stream_id, 'type' : 'dest', "noc0_x" : noc0_x, "noc0_y" : noc0_y, \
                'cmd' : f"s {noc0_x} {noc0_y} {reg_strings['REMOTE_DEST_STREAM_ID']}" })
        if regs["LOCAL_SOURCES_CONNECTED"]!=0:
            val += "LSC "

        if not idle:
            all_streams_summary[f"{stream_id}"] = val
        else:
            val += "idle"
    return all_streams_summary, navigation_suggestions

#
# Analysis functions
#


# Detects potential problems within all chip streams, and prints a summary
def stream_summary(chip, x_coords, y_coords, streams, short=False):
    active_streams = {}
    bad_streams = []
    gsync_hung = {}
    ncrisc_done = {}

    # Detect problems
    for x in x_coords:
        active_streams[x] = {}
        gsync_hung[x] = {}
        ncrisc_done[x] = {}
        for y in y_coords:
            active_streams[x][y] = []
            for stream_id in range (0, 64):
                if is_stream_active(streams[x][y][stream_id]):
                    active_streams[x][y].append(stream_id)
                if is_bad_stream(streams[x][y][stream_id]):
                    bad_streams.append([x,y,stream_id])
            gsync_hung[x][y] = is_gsync_hung(chip, x, y)
            ncrisc_done[x][y] = is_ncrisc_done(chip, x, y)

    # Print streams that are not idle
    all_streams_done = True
    headers = [ "X-Y", "Op", "Stream", "Type", "Epoch", "Phase", "State", "CURR_PHASE_NUM_MSGS_REMAINING", "NUM_MSGS_RECEIVED" ]
    rows = []

    for x in x_coords:
        for y in y_coords:
            if len(active_streams[x][y]) != 0:
                first_stream = True

                for i in range(len(active_streams[x][y])):
                    xy = f"{x}-{y}" if first_stream else ""
                    first_stream = False
                    stream_id=active_streams[x][y][i]
                    current_phase = int(streams[x][y][stream_id]['CURR_PHASE'])
                    epoch_id = current_phase>>10
                    stream_type_str = stream_type(stream_id)["short"]
                    op = core_coord_to_op_name(EPOCH_ID_TO_GRAPH_NAME[epoch_id], x, y)
                    row = [ xy, op, stream_id, stream_type_str, epoch_id, current_phase, f"{util.CLR_WARN}Active{util.CLR_END}", int(streams[x][y][stream_id]['CURR_PHASE_NUM_MSGS_REMAINING']), int(streams[x][y][stream_id]['NUM_MSGS_RECEIVED']) ]
                    rows.append (row)
                    all_streams_done = False

    if not all_streams_done:
        print (tabulate(rows, headers=headers))
    if all_streams_done:
        print("  No streams appear hung. If the test hung, some of the streams possibly did not get any tiles.")

    # Print streams in bad state
    if len(bad_streams) != 0:
        print()
        print("The following streams are in a bad state (have an assertion in DEBUG_STATUS[1], or DEBUG_STATUS[2] indicates a hang):")
        for i in range(len(bad_streams)):
            bad_stream_x = bad_streams[i][0]
            bad_stream_y = bad_streams[i][1]
            bad_stream_id = bad_streams[i][2]
            print(f"\t x={bad_stream_x:02d}, y={bad_stream_y:02d}, stream_id={bad_stream_id:02d}")

    # Print gsync_hung cores
    for x in x_coords:
        for y in y_coords:
            if gsync_hung[x][y]:
                print(f"Global sync hang: x={x:02d}, y={y:02d}")

    # Print NC Riscs that are not idle
    if all_streams_done: # Only do this if all streams are done
        ncriscs_not_idle_count = 0
        for y in y_coords:
            for x in x_coords:
                if not ncrisc_done[x][y]:
                    if ncriscs_not_idle_count == 0: # First output
                        print("NCRISCs not idle: ")
                    ncriscs_not_idle_count += 1
                    print(f"{x:02d}-{y:02d}", end=" ")
                    if ncriscs_not_idle_count % 12 == 0:
                        print()
        if ncriscs_not_idle_count > 0:
            print()

# Prints all information on a stream
def print_stream (current_chip, x, y, stream_id, current_epoch_id):
    regs = grayskull.read_stream_regs (current_chip, x, y, stream_id)
    stream_regs = convert_reg_dict_to_strings(current_chip, regs, x, y, stream_id)
    streams_from_blob = get_streams_from_blob (current_chip, x, y, stream_id)
    stream_epoch_id = (regs["CURR_PHASE"] >> 10)
    current_epoch_id = stream_epoch_id

    all_stream_summary, navigation_suggestions = get_core_stream_summary (current_chip, x, y)
    data_columns = [ all_stream_summary ] if len(all_stream_summary) > 0 else []
    title_columns = [ f"{util.CLR_WARN}Non-idle streams{util.CLR_END}" ] if len(all_stream_summary) > 0 else []

    data_columns.append (stream_regs)
    title_columns.append ("Registers")

    # 1. Append blobs
    buffer_id_strings = set()
    non_active_phases = dict()
    for stream_from_blob in streams_from_blob:
        buf_id = stream_from_blob["buf_id"] if stream_from_blob and "buf_id" in stream_from_blob else None
        if f"{regs['CURR_PHASE']}" in stream_from_blob["source"]:
            if buf_id is not None:
                buffer_str = f"buffer_{buf_id}"
                buffer_id_strings.add (buffer_str)
            data_columns.append (stream_from_blob)
            title_columns.append ("Stream (blob.yaml)")
        else:
            non_active_phases[stream_from_blob["source"]] = "-"

    # 1a. Print Non Active phases, if any
    if len(non_active_phases) > 0:
        title_columns.append ("non-active phases")
        data_columns.append (non_active_phases)

    # 2. Append buffers
    for buffer_id_string in buffer_id_strings:
        data_columns.append (PIPEGEN[buffer_id_string] if buffer_id_string in PIPEGEN else { "-": "-" })
        title_columns.append (buffer_id_string)

    # 3. Append relevant pipes
    for buffer_id_string in buffer_id_strings:
        buffer_id = int (buffer_id_string[7:], 0) # HACK: to skip the "buffer_" string
        # FIX: below is mostly copied from print_buffer_data()
        for epoch_id in EPOCH_TO_PIPEGEN_YAML_MAP:
            for dct in EPOCH_TO_PIPEGEN_YAML_MAP[epoch_id]:
                d = EPOCH_TO_PIPEGEN_YAML_MAP[epoch_id][dct]
                if ("input_list" in d and buffer_id in d["input_list"]) or ("output_list" in d and buffer_id in d["output_list"]):
                    data_columns.append (d)
                    title_columns.append ("Pipe")

    util.print_columnar_dicts (data_columns, title_columns)

    if current_epoch_id != stream_epoch_id:
        print (f"{util.CLR_WARN}Current epoch is {current_epoch_id}, while the stream is in epoch {stream_epoch_id} {util.CLR_END}. To switch to epoch {stream_epoch_id}, enter {util.CLR_PROMPT}e {stream_epoch_id}{util.CLR_END}")

    # 4. TODO: Print forks

    return navigation_suggestions, stream_epoch_id

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

# Given a dict returned by grayskull.read_stream_regs, convert to strings (and colorize)
def convert_reg_dict_to_strings(device, regs):
    string_regs = {}
    for k in regs:
        # Convert to strings
        string_regs[k] = get_as_str (k, regs[k])
        # If on noc-1, convert the coords no noc-0 coords
        if "REMOTE_SRC_UPDATE_NOC" in regs and regs["REMOTE_SRC_UPDATE_NOC"] > 0:
            try:
                if k == "REMOTE_SRC_X":
                    noc0_x, noc0_y = device.noc1_to_noc0 (regs[k], 0)
                    string_regs[k] += f"({util.CLR_INFO}{noc0_x}{util.CLR_END})"
                if k == "REMOTE_SRC_Y":
                    noc0_x, noc0_y = device.noc1_to_noc0 (0, regs[k])
                    string_regs[k] += f"({util.CLR_INFO}{noc0_y}{util.CLR_END})"
            except:
                print (f"{util.CLR_ERR}Invalid coordinate passed k={k} regs[k]={regs[k]} {util.CLR_END}")
                raise

    return string_regs

def get_epoch_id (stream_regs):
    stream_epoch_id = (stream_regs["CURR_PHASE"] >> 10)

#
# Object
#
class Stream:
    # Return (chip_id, noc0_X, noc0_Y, stream_id) given a designator from blob.yaml
    def get_stream_tuple_from_designator (designator):
        # Example full name: chip_0__y_1__x_1__stream_id_8
        vals = re.findall(r'chip_(\d+)__y_(\d+)__x_(\d+)__stream_id_(\d+)', designator)
        # print (f"{designator}, {vals}")
        return ( int(vals[0][0]), int (vals[0][2]), int (vals[0][1]), int (vals[0][3]) )

    def __init__(self, designator, data):
        self.designator = designator
        self.location = Stream.get_stream_tuple_from_designator (designator)
        self._id = self.location + ( data['phase_id'], )
        self.root = data

    # Accessors
    def id (self):
        return self._id
    # def inputs(self):
    #     return None
    # def outputs(self):
    #     return None

    # Renderer
    def __str__(self):
        return f"{type(self).__name__}: id: {self.id()}"