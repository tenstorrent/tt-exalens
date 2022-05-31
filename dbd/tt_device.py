import os, subprocess, time, struct, signal, re, zmq
from tabulate import tabulate
import tt_util as util
STUB_HELP = "This tool requires debuda-stub. You can build debuda-stub with bin/build-debuda-stub.sh. It also requires zeromq (sudo apt install -y libzmq3-dev)."

#
# Communication with Buda (or debuda-stub) over sockets (ZMQ).
# See struct BUDA_READ_REQ for protocol details
#
ZMQ_SOCKET=None              # The socket for communication
DEBUDA_STUB_PROCESS_ID=None  # The process ID of debuda-stub spawned in init_comm_client

# Spawns debuda-stub and initializes the communication
def init_comm_client (debug_debuda_stub):
    DEBUDA_STUB_PORT=5555

    print ("Spawning debuda-stub...")

    debuda_stub_path = util.application_path() + "/debuda-stub"
    try:
        global DEBUDA_STUB_PROCESS_ID
        debuda_stub_args = [ "--debug" ] if debug_debuda_stub else [ ]
        # print ("debuda_stub_cmd = %s" % ([debuda_stub_path] + debuda_stub_args))
        DEBUDA_STUB_PROCESS_ID=subprocess.Popen([debuda_stub_path] + debuda_stub_args, preexec_fn=os.setsid)
    except:
        print (f"Exception: {util.CLR_ERR} Cannot find {debuda_stub_path}. {STUB_HELP} {util.CLR_END}")
        raise

    context = zmq.Context()
    global ZMQ_SOCKET

    time.sleep (0.1) # Cosmetic wait: To allow debuda-stub to print the message

    #  Socket to talk to server
    print("Connecting to debuda-stub...")
    ZMQ_SOCKET = context.socket(zmq.REQ)
    ZMQ_SOCKET.connect(f"tcp://localhost:{DEBUDA_STUB_PORT}")
    print("Connected to debuda-stub.")

    ZMQ_SOCKET.send(struct.pack ("c", b'\x01')) # PING
    reply = ZMQ_SOCKET.recv_string()
    if "PONG" not in reply:
        print (f"Expected PONG but received {reply}") # Should print PONG

    time.sleep (0.1)

# Terminates debuda-stub spawned in init_comm_client
def terminate_comm_client_callback ():
    os.killpg(os.getpgid(DEBUDA_STUB_PROCESS_ID.pid), signal.SIGTERM)
    print (f"Terminated debuda-stub with pid:{DEBUDA_STUB_PROCESS_ID.pid}")

# PCI read/write functions. Given a noc0 location and addr, performs a PCI read/write
# to the given location at the address.
def pci_read_xy(chip_id, x, y, noc_id, reg_addr):
    # print (f"Reading {x}-{y} 0x{reg_addr:x}")
    # ZMQ_SOCKET.send(struct.pack ("ccccci", b'\x02', chip_id, x, y, z, reg_addr))
    ZMQ_SOCKET.send(struct.pack ("cccccII", b'\x02', chip_id.to_bytes(1, byteorder='big'), x.to_bytes(1, byteorder='big'), y.to_bytes(1, byteorder='big'), noc_id.to_bytes(1, byteorder='big'), reg_addr, 0))
    ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
    return ret_val
def pci_write_xy(chip_id, x, y, noc_id, reg_addr, data):
    # print (f"Reading {x}-{y} 0x{reg_addr:x}")
    # ZMQ_SOCKET.send(struct.pack ("ccccci", b'\x02', chip_id, x, y, z, reg_addr))
    ZMQ_SOCKET.send(struct.pack ("cccccII", b'\x04', chip_id.to_bytes(1, byteorder='big'), x.to_bytes(1, byteorder='big'), y.to_bytes(1, byteorder='big'), noc_id.to_bytes(1, byteorder='big'), reg_addr, data))
    ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
    assert data == ret_val
def host_dma_read (dram_addr):
    # print ("host_dma_read 0x%x" % dram_addr)
    ZMQ_SOCKET.send(struct.pack ("cccccI", b'\x03', b'\x00', b'\x00', b'\x00', b'\x00', dram_addr))
    ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
    return ret_val
def pci_read_tile(chip_id, x, y, z, reg_addr, msg_size, data_format):
    # print (f"Reading {x}-{y} 0x{reg_addr:x}")
    # ZMQ_SOCKET.send(struct.pack ("ccccci", b'\x05', chip_id, x, y, z, reg_addr, data_format<<16 + message_size))
    data = data_format * 2**16 + msg_size
    ZMQ_SOCKET.send(struct.pack ("cccccII", b'\x05', chip_id.to_bytes(1, byteorder='big'), x.to_bytes(1, byteorder='big'), y.to_bytes(1, byteorder='big'), z.to_bytes(1, byteorder='big'), reg_addr, data))
    ret = ZMQ_SOCKET.recv()
    return ret

# Prints contents of core's memory
def dump_memory(device_id, x, y, addr, size):
    for k in range(0, size//4//16 + 1):
        row = []
        for j in range(0, 16):
            if (addr + k*64 + j* 4 < addr + size):
                val = pci_read_xy(device_id, x, y, 0, addr + k*64 + j*4)
                row.append(f"0x{val:08x}")
        s = " ".join(row)
        print(f"{x}-{y} 0x{(addr + k*64):08x} => {s}")

# Dumps tile in format received form tt_tile::get_string
def dump_tile(chip, x, y, addr, size, data_format):
    s = pci_read_tile(chip, x, y, 0, addr, size, data_format)
    print(s.decode("utf-8"))

#
# Device class: generic constructs for talking to devices
#
class Device:
    # Class variable denoting the number of devices created
    num_devices = 0

    # Class method to create a Device object given device architecture
    def create(arch):
        dev = None
        if arch.lower() == "grayskull":
            import tt_grayskull
            dev = tt_grayskull.GrayskullDevice()
        if arch.lower() == "wormhole":
            import tt_wormhole
            dev = tt_wormhole.WormholeDevice()

        if dev is None:
            raise RuntimeError(f"Architecture {arch} not supported yet")

        dev._id = Device.num_devices
        dev.arch = arch
        Device.num_devices+=1
        return dev

    def __init__(self, arch):
        raise RuntimeError(f"Use Device.create class method to create a device")

    # Accessors
    def id (self):
        return self._id

    # For all cores read all 64 streams and populate the 'streams' dict. streams[x][y][stream_id] will
    # contain a dictionary of all register values as strings formatted to show in UI
    def read_all_stream_registers (self):
        streams = {}
        for loc in self.get_block_locations (block_type = "functional_workers"):
            for stream_id in range (0, 64):
                regs = self.read_stream_regs (loc, stream_id)
                streams[loc + (stream_id,)] = regs
        return streams

    # For a given core, read all 64 streams and populate the 'streams' dict. streams[stream_id] will
    # contain a dictionary of all register values as strings formatted to show in UI
    def read_core_stream_registers (self, loc):
        streams = {}
        for stream_id in range (0, 64):
            regs = self.read_stream_regs (loc, stream_id)
            streams[stream_id] = regs
        return streams

    # Returns core locations of cores that have programmed stream registers
    def get_configured_stream_locations(self, all_stream_regs):
        core_locations = []
        for loc, stream_regs in all_stream_regs.items():
            if self.is_stream_configured(stream_regs):
                core_locations.append (loc)
        return core_locations

    #  Returns locations of all blocks of a given type
    def get_block_locations (self, block_type = "functional_workers"):
        locs = []
        dev = self.yaml_file.root
        for loc in dev[block_type]:
            if type(loc) == list:
                loc = loc[0]
            parsed_loc = re.findall(r'(\d+)-(\d+)', loc)
            parsed_loc = re.findall(r'(\d+)-(\d+)', loc)
            x = int(parsed_loc[0][0])
            y = int(parsed_loc[0][1])
            locs.append ((x,y))
        return locs

    # Returns a string representation of the device. When printed, the string will
    # show the device blocks ascii graphically. It will emphasize blocks with locations given by emphasize_loc_list
    def render (self, options="physical", emphasize_noc0_loc_list = set(), emphasize_explanation = None):
        dev = self.yaml_file.root
        rows = []
        locs = dict()
        emphasize_loc_list_to_render = set()

        # Convert emphasize_noc0_loc_list from noc0 coordinates to the coord space given by 'options' arg
        if options=="physical":
            for loc in emphasize_noc0_loc_list:
                emphasize_loc_list_to_render.add (self.noc_to_physical(loc, noc_id=0))
        elif options=="rc":
            for loc in emphasize_noc0_loc_list:
                emphasize_loc_list_to_render.add (self.noc0_to_rc(loc[0], loc[1]))
        elif options=="noc0":
            emphasize_loc_list_to_render = emphasize_noc0_loc_list
        else:
            util.ERROR (f"Invalid options: {options}")

        block_types = { 'functional_workers' : { 'symbol' : '.', "desc" : "Functional worker" },
                        'eth':                 { 'symbol' : 'E', "desc" : "Ethernet" },
                        'arc' :                { 'symbol' : 'A', "desc" : "ARC" },
                        'dram' :               { 'symbol' : 'D', "desc" : "DRAM" },
                        'pcie' :               { 'symbol' : 'P', "desc" : "PCIE" },
                        'router_only' :        { 'symbol' : ' ', "desc" : "Router only" }
        }

        block_types_present = set()

        # Convert the block locations to the coord space given by 'options' arg
        for block_name in block_types:
            if options=="rc" and block_name != 'functional_workers': continue  # No blocks other than Tensix cores have RC coords
            for loc in self.get_block_locations (block_name):
                if options=="physical":
                    loc = self.noc_to_physical(loc, noc_id=0)
                elif options=="rc":
                    loc = self.noc0_to_rc(loc[0], loc[1])
                locs[loc] = block_types[block_name]['symbol']
                block_types_present.add(block_name)

        # Render the grid
        x_size = dev['grid']['x_size']
        y_size = dev['grid']['y_size']

        if options == "rc":
            y_size-=self.rows_with_no_functional_workers() # GS:2, WH:2
            x_size-=self.cols_with_no_functional_workers() # GS:1, WH:2

        legend = [ f"Coordinate system: {options}", "Legend:" ] + [ f"{block_types[block_type]['symbol']} - {block_types[block_type]['desc']}" for block_type in block_types_present ]
        if emphasize_explanation is not None:
            legend += [ "+ - " + emphasize_explanation ]

        for y in reversed(range (y_size)): # We want 0,0 in the bottom left corner, so we reverse
            row = [ f"%02d" % y ]
            # 1. Add graphics
            for x in range (x_size):
                render_str = ""
                if options=="rc":
                    rc_loc = (y, x)
                    if rc_loc in locs: render_str += locs[rc_loc]
                    if rc_loc in emphasize_loc_list_to_render: render_str = "+"
                else:
                    if (x,y) in locs: render_str += locs[(x,y)]
                    if (x,y) in emphasize_loc_list_to_render: render_str = "+"
                row.append (render_str)

            # 2. Add legend
            legend_y = y_size - y - 1
            if legend_y < len(legend):
                row = row + [ util.CLR_INFO + legend[legend_y] + util.CLR_END ]

            rows.append (row)
        row = [ "" ] + [ f"%02d" % i for i in range(x_size) ]
        rows.append (row)

        table_str = tabulate(rows, tablefmt='plain')
        return table_str 

    def dump_memory(self, x, y, addr, size):
        return dump_memory(self.id(), x, y, addr, size)
    def dump_tile(self, x, y, addr, size, data_format):
        return dump_tile(self.id(), x, y, addr, size, data_format)

    def __str__(self):
        return self.render()

    # Reads and returns the Risc debug registers
    def get_debug_regs(self, x, y):
        DEBUG_MAILBOX_BUF_BASE  = 112
        DEBUG_MAILBOX_BUF_SIZE  = 64
        THREAD_COUNT = 4

        debug_tables = [ [] for i in range (THREAD_COUNT) ]
        for thread_idx in range (THREAD_COUNT):
            for reg_idx in range(DEBUG_MAILBOX_BUF_SIZE // THREAD_COUNT):
                reg_addr = DEBUG_MAILBOX_BUF_BASE + thread_idx * DEBUG_MAILBOX_BUF_SIZE + reg_idx * 4
                val = pci_read_xy(self.id(), x, y, 0, reg_addr)
                debug_tables[thread_idx].append ({ "lo_val" : val & 0xffff, "hi_val": (val >> 16) & 0xffff })
        return debug_tables