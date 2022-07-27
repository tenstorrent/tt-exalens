import os, subprocess, time, struct, signal, re, zmq, pickle
from tabulate import tabulate
from dbd.tt_object import TTObject
import tt_util as util
import tt_object
STUB_HELP = "This tool requires debuda-stub. You can build debuda-stub with 'make dbd/debuda-stub'. It also requires zeromq (sudo apt install -y libzmq3-dev)."

#
# Communication with Buda (or debuda-stub) over sockets (ZMQ).
# See struct BUDA_READ_REQ for protocol details
#
ZMQ_SOCKET=None              # The socket for communication
DEBUDA_STUB_PROCESS=None  # The process ID of debuda-stub spawned in init_comm_client

# Spawns debuda-stub and initializes the communication
def init_comm_client (ip="localhost", port=5555, debug_debuda_stub=False):
    debuda_stub_address=f"tcp://{ip}:{port}"
    spawning_debuda_stub = ip=='localhost'

    if spawning_debuda_stub:
        print ("Spawning debuda-stub...")

        debuda_stub_path = util.application_path() + "/../build/bin/debuda-stub"
        try:
            global DEBUDA_STUB_PROCESS
            debuda_stub_args = [ "--debug" ] if debug_debuda_stub else [ ]
            debuda_stub_args += [ "--port", f"{port}"]

            # print ("debuda_stub_cmd = %s" % ([debuda_stub_path] + debuda_stub_args))
            DEBUDA_STUB_PROCESS=subprocess.Popen([debuda_stub_path] + debuda_stub_args, preexec_fn=os.setsid)
        except:
            print (f"Exception: {util.CLR_ERR} Cannot find {debuda_stub_path}. {STUB_HELP} {util.CLR_END}")
            raise
        time.sleep (0.1) # Cosmetic wait: To allow debuda-stub to print the message
        debuda_stub_is_running = DEBUDA_STUB_PROCESS.poll() is None
        if not debuda_stub_is_running:
            util.ERROR ("Debuda stub could not be spawned on localhost")

    print(f"Connecting to local debuda-stub at {debuda_stub_address}...")

    context = zmq.Context()
    global ZMQ_SOCKET

    try:
        #  Socket to talk to server
        ZMQ_SOCKET = context.socket(zmq.REQ)
        ZMQ_SOCKET.connect(debuda_stub_address)

        ZMQ_SOCKET.send(struct.pack ("c", b'\x01')) # PING
        reply = ZMQ_SOCKET.recv_string()
        if "PONG" not in reply:
            print (f"Expected PONG but received {reply}") # Should print PONG

        print("Connected to debuda-stub.")
    except:
        if spawning_debuda_stub:
            terminate_comm_client_callback ()
        raise

    time.sleep (0.1)

# Terminates debuda-stub spawned in init_comm_client
def terminate_comm_client_callback ():
    if DEBUDA_STUB_PROCESS is not None and DEBUDA_STUB_PROCESS.poll() is None:
        os.killpg(os.getpgid(DEBUDA_STUB_PROCESS.pid), signal.SIGTERM)
        util.VERBOSE (f"Terminated debuda-stub")

# This is the interface to the debuda server (aka. debuda-stub)
class DEBUDA_SERVER_IFC:
    enabled = True # It can be disabled for offline operation (when working from cache)

    NOT_ENABLED_ERROR_MSG="Access to device/host is requested, while the device communication is disabled with --server-cache"

    # PCI read/write functions. Given a noc0 location and addr, performs a PCI read/write
    # to the given location at the address.
    def pci_read_xy(chip_id, x, y, noc_id, reg_addr):
        assert DEBUDA_SERVER_IFC.enabled, DEBUDA_SERVER_IFC.NOT_ENABLED_ERROR_MSG
        # print (f"Reading {util.noc_loc_str((x, y))} 0x{reg_addr:x}")
        # ZMQ_SOCKET.send(struct.pack ("ccccci", b'\x02', chip_id, x, y, z, reg_addr))
        ZMQ_SOCKET.send(struct.pack ("cccccII", b'\x02', chip_id.to_bytes(1, byteorder='big'), x.to_bytes(1, byteorder='big'), y.to_bytes(1, byteorder='big'), noc_id.to_bytes(1, byteorder='big'), reg_addr, 0))
        ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
        return ret_val
    def pci_write_xy(chip_id, x, y, noc_id, reg_addr, data):
        assert DEBUDA_SERVER_IFC.enabled, DEBUDA_SERVER_IFC.NOT_ENABLED_ERROR_MSG
        # print (f"Reading {util.noc_loc_str((x, y))} 0x{reg_addr:x}")
        # ZMQ_SOCKET.send(struct.pack ("ccccci", b'\x02', chip_id, x, y, z, reg_addr))
        ZMQ_SOCKET.send(struct.pack ("cccccII", b'\x04', chip_id.to_bytes(1, byteorder='big'), x.to_bytes(1, byteorder='big'), y.to_bytes(1, byteorder='big'), noc_id.to_bytes(1, byteorder='big'), reg_addr, data))
        ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
        assert data == ret_val
    def host_dma_read (dram_addr):
        assert DEBUDA_SERVER_IFC.enabled, DEBUDA_SERVER_IFC.NOT_ENABLED_ERROR_MSG
        # print ("host_dma_read 0x%x" % dram_addr)
        ZMQ_SOCKET.send(struct.pack ("cccccI", b'\x03', b'\x00', b'\x00', b'\x00', b'\x00', dram_addr))
        ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
        return ret_val
    def pci_read_tile(chip_id, x, y, z, reg_addr, msg_size, data_format):
        assert DEBUDA_SERVER_IFC.enabled, DEBUDA_SERVER_IFC.NOT_ENABLED_ERROR_MSG
        # print (f"Reading {util.noc_loc_str((x, y))} 0x{reg_addr:x}")
        # ZMQ_SOCKET.send(struct.pack ("ccccci", b'\x05', chip_id, x, y, z, reg_addr, data_format<<16 + message_size))
        data = data_format * 2**16 + msg_size
        ZMQ_SOCKET.send(struct.pack ("cccccII", b'\x05', chip_id.to_bytes(1, byteorder='big'), x.to_bytes(1, byteorder='big'), y.to_bytes(1, byteorder='big'), z.to_bytes(1, byteorder='big'), reg_addr, data))
        ret = ZMQ_SOCKET.recv()
        return ret
    def pci_raw_read(chip_id, reg_addr):
        assert DEBUDA_SERVER_IFC.enabled, DEBUDA_SERVER_IFC.NOT_ENABLED_ERROR_MSG
        zero = 0
        ZMQ_SOCKET.send(struct.pack ("cccccII", b'\x06', chip_id.to_bytes(1, byteorder='big'), zero.to_bytes(1, byteorder='big'), zero.to_bytes(1, byteorder='big'), zero.to_bytes(1, byteorder='big'), reg_addr, 0))
        ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
        return ret_val
    def pci_raw_write(chip_id, reg_addr, data):
        assert DEBUDA_SERVER_IFC.enabled, DEBUDA_SERVER_IFC.NOT_ENABLED_ERROR_MSG
        ZMQ_SOCKET.send(struct.pack ("cccccII", b'\x07', chip_id.to_bytes(1, byteorder='big'), zero.to_bytes(1, byteorder='big'), zero.to_bytes(1, byteorder='big'), zero.to_bytes(1, byteorder='big'), reg_addr, data))
        ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
        assert data == ret_val

# This interface is used to read cached values of PCI reads.
class DEBUDA_SERVER_CACHED_IFC:
    filepath = 'debuda-server-cache.pkl'
    cache_store = dict()
    enabled = True

    def load ():
        if DEBUDA_SERVER_CACHED_IFC.enabled:
            if os.path.exists (DEBUDA_SERVER_CACHED_IFC.filepath):
                util.VERBOSE (f"Loading server cache from file {DEBUDA_SERVER_CACHED_IFC.filepath}")
                with open(DEBUDA_SERVER_CACHED_IFC.filepath, 'rb') as f:
                    DEBUDA_SERVER_CACHED_IFC.cache_store = pickle.load(f)
            else:
                assert DEBUDA_SERVER_IFC.enabled, f"Cache file {DEBUDA_SERVER_CACHED_IFC.filepath} does not exist"

    def save():
        if DEBUDA_SERVER_CACHED_IFC.enabled and DEBUDA_SERVER_IFC.enabled:
            util.VERBOSE (f"Saving server cache to file {DEBUDA_SERVER_CACHED_IFC.filepath}")
            with open(DEBUDA_SERVER_CACHED_IFC.filepath, 'wb') as f:
                pickle.dump(DEBUDA_SERVER_CACHED_IFC.cache_store, f)

    def pci_read_xy(chip_id, x, y, noc_id, reg_addr):
        key = (chip_id, x, y, noc_id, reg_addr)
        if key not in DEBUDA_SERVER_CACHED_IFC.cache_store or not DEBUDA_SERVER_CACHED_IFC.enabled:
            DEBUDA_SERVER_CACHED_IFC.cache_store[key] = DEBUDA_SERVER_IFC.pci_read_xy(chip_id, x, y, noc_id, reg_addr)
        return DEBUDA_SERVER_CACHED_IFC.cache_store[key]
    def pci_write_xy(chip_id, x, y, noc_id, reg_addr, data):
        if not DEBUDA_SERVER_CACHED_IFC.enabled:
            return DEBUDA_SERVER_IFC.pci_write_xy(chip_id, x, y, noc_id, reg_addr, data)
    def host_dma_read (dram_addr):
        key = (dram_addr)
        if key not in DEBUDA_SERVER_CACHED_IFC.cache_store or not DEBUDA_SERVER_CACHED_IFC.enabled:
            DEBUDA_SERVER_CACHED_IFC.cache_store[key] = DEBUDA_SERVER_IFC.host_dma_read (dram_addr)
        return DEBUDA_SERVER_CACHED_IFC.cache_store[key]
    def pci_read_tile(chip_id, x, y, z, reg_addr, msg_size, data_format):
        key = (chip_id, x, y, z, reg_addr, msg_size, data_format)
        if key not in DEBUDA_SERVER_CACHED_IFC.cache_store or not DEBUDA_SERVER_CACHED_IFC.enabled:
            DEBUDA_SERVER_CACHED_IFC.cache_store[key] = DEBUDA_SERVER_IFC.pci_read_tile(chip_id, x, y, z, reg_addr, msg_size, data_format)
        return DEBUDA_SERVER_CACHED_IFC.cache_store[key]
    def pci_raw_read(chip_id, reg_addr):
        key = (chip_id, reg_addr)
        if key not in DEBUDA_SERVER_CACHED_IFC.cache_store or not DEBUDA_SERVER_CACHED_IFC.enabled:
            DEBUDA_SERVER_CACHED_IFC.cache_store[key] = DEBUDA_SERVER_IFC.pci_raw_read(chip_id, reg_addr)
        return DEBUDA_SERVER_CACHED_IFC.cache_store[key]
    def pci_raw_write(chip_id, reg_addr, data):
        if not DEBUDA_SERVER_CACHED_IFC.enabled:
            return DEBUDA_SERVER_IFC.pci_raw_write(chip_id, reg_addr, data)

# PCI interface is a cached interface through Debuda server
class PCI_IFC (DEBUDA_SERVER_CACHED_IFC):
    pass

# Prints contents of core's memory
def dump_memory(device_id, noc0_loc, addr, size):
    for k in range(0, size//4//16 + 1):
        row = []
        for j in range(0, 16):
            if (addr + k*64 + j* 4 < addr + size):
                val = PCI_IFC.pci_read_xy(device_id, *noc0_loc, 0, addr + k*64 + j*4)
                row.append(f"0x{val:08x}")
        s = " ".join(row)
        print(f"{util.noc_loc_str(noc0_loc)} 0x{(addr + k*64):08x} => {s}")

# Dumps tile in format received form tt_tile::get_string
def dump_tile(chip, noc0_loc, addr, size, data_format):
    s = PCI_IFC.pci_read_tile(chip, *noc0_loc, 0, addr, size, data_format)
    print(s.decode("utf-8"))

#
# Device class: generic constructs for talking to devices
#
class Device(TTObject):
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

    # Coordinate conversion functions
    def physical_to_noc (self, phys_loc, noc_id=0):
        phys_x, phys_y = phys_loc
        if noc_id == 0:
            return (self.PHYS_X_TO_NOC_0_X[phys_x], self.PHYS_Y_TO_NOC_0_Y[phys_y])
        else:
            return (self.PHYS_X_TO_NOC_1_X[phys_x], self.PHYS_Y_TO_NOC_1_Y[phys_y])

    def noc_to_physical (self, noc_loc, noc_id=0):
        noc_x, noc_y = noc_loc
        if noc_id == 0:
            return (self.NOC_0_X_TO_PHYS_X[noc_x], self.NOC_0_Y_TO_PHYS_Y[noc_y])
        else:
            return (self.NOC_1_X_TO_PHYS_X[noc_x], self.NOC_1_Y_TO_PHYS_Y[noc_y])

    def noc0_to_noc1 (self, noc0_loc):
        phys_loc = self.noc_to_physical (noc0_loc, noc_id=0)
        return self.physical_to_noc (phys_loc, noc_id=1)

    def noc1_to_noc0 (self, noc1_loc):
        phys_loc = self.noc_to_physical (noc1_loc, noc_id=1)
        return self.physical_to_noc (phys_loc, noc_id=0)

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
    def render (self, options="physical", emphasize_noc0_loc_list = util.set(), emphasize_explanation = None):
        dev = self.yaml_file.root
        rows = []
        locs = dict()
        emphasize_loc_list_to_render = util.set()

        # Convert emphasize_noc0_loc_list from noc0 coordinates to the coord space given by 'options' arg
        if options=="physical":
            for loc in emphasize_noc0_loc_list:
                emphasize_loc_list_to_render.add (self.noc_to_physical(loc, noc_id=0))
        elif options=="rc":
            for loc in emphasize_noc0_loc_list:
                emphasize_loc_list_to_render.add (self.noc0_to_rc(loc))
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

        block_types_present = util.set()

        # Convert the block locations to the coord space given by 'options' arg
        for block_name in block_types:
            if options=="rc" and block_name != 'functional_workers': continue  # No blocks other than Tensix cores have RC coords
            for loc in self.get_block_locations (block_name):
                if options=="physical":
                    loc = self.noc_to_physical(loc, noc_id=0)
                elif options=="rc":
                    loc = self.noc0_to_rc(loc)
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

        rng = range (y_size) if options == 'rc' else reversed(range (y_size))
        for y in rng:
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

    def dump_memory(self, noc0_loc, addr, size):
        return dump_memory(self.id(), noc0_loc, addr, size)
    def dump_tile(self, noc0_loc, addr, size, data_format):
        return dump_tile(self.id(), noc0_loc, addr, size, data_format)

    def __str__(self):
        return self.render()

    # Reads and returns the Risc debug registers
    def get_debug_regs(self, noc0_loc):
        DEBUG_MAILBOX_BUF_BASE  = 112
        DEBUG_MAILBOX_BUF_SIZE  = 64
        THREAD_COUNT = 4

        debug_tables = [ [] for i in range (THREAD_COUNT) ]
        for thread_idx in range (THREAD_COUNT):
            for reg_idx in range(DEBUG_MAILBOX_BUF_SIZE // THREAD_COUNT):
                reg_addr = DEBUG_MAILBOX_BUF_BASE + thread_idx * DEBUG_MAILBOX_BUF_SIZE + reg_idx * 4
                val = PCI_IFC.pci_read_xy(self.id(), *noc0_loc, 0, reg_addr)
                debug_tables[thread_idx].append ({ "lo_val" : val & 0xffff, "hi_val": (val >> 16) & 0xffff })
        return debug_tables

    # Returns a stream type based on KERNEL_OPERAND_MAPPING_SCHEME
    def stream_type (self, stream_id):
        # From src/firmware/riscv/grayskull/stream_io_map.h
        # Kernel operand mapping scheme:
        KERNEL_OPERAND_MAPPING_SCHEME = [
            { "id_min" : 0,  "id_max" : 7,  "stream_id_min" : 0, "short" : "??", "long" : "????? => streams 0-7" }, # FIX THIS
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


    # Function to print a full dump of a location x-y
    def full_dump_xy(self, noc0_loc):
        for stream_id in range (0, 64):
            print()
            stream = self.read_stream_regs(noc0_loc, stream_id)
            for reg, value in stream.items():
                print(f"Tensix x={noc0_loc[0]:02d},y={noc0_loc[1]:02d} => stream {stream_id:02d} {reg} = {value}")

        for noc_id in range (0, 2):
            print()
            self.read_print_noc_reg(noc0_loc, noc_id, "nonposted write reqs sent", 0xA)
            self.read_print_noc_reg(noc0_loc, noc_id, "posted write reqs sent", 0xB)
            self.read_print_noc_reg(noc0_loc, noc_id, "nonposted write words sent", 0x8)
            self.read_print_noc_reg(noc0_loc, noc_id, "posted write words sent", 0x9)
            self.read_print_noc_reg(noc0_loc, noc_id, "write acks received", 0x1)
            self.read_print_noc_reg(noc0_loc, noc_id, "read reqs sent", 0x5)
            self.read_print_noc_reg(noc0_loc, noc_id, "read words received", 0x3)
            self.read_print_noc_reg(noc0_loc, noc_id, "read resps received", 0x2)
            print()
            self.read_print_noc_reg(noc0_loc, noc_id, "nonposted write reqs received", 0x1A)
            self.read_print_noc_reg(noc0_loc, noc_id, "posted write reqs received", 0x1B)
            self.read_print_noc_reg(noc0_loc, noc_id, "nonposted write words received", 0x18)
            self.read_print_noc_reg(noc0_loc, noc_id, "posted write words received", 0x19)
            self.read_print_noc_reg(noc0_loc, noc_id, "write acks sent", 0x10)
            self.read_print_noc_reg(noc0_loc, noc_id, "read reqs received", 0x15)
            self.read_print_noc_reg(noc0_loc, noc_id, "read words sent", 0x13)
            self.read_print_noc_reg(noc0_loc, noc_id, "read resps sent", 0x12)
            print()
            self.read_print_noc_reg(noc0_loc, noc_id, "router port x out vc full credit out vc stall", 0x24)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port y out vc full credit out vc stall", 0x22)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port niu out vc full credit out vc stall", 0x20)
            print()
            self.read_print_noc_reg(noc0_loc, noc_id, "router port x VC14 & VC15 dbg", 0x3d)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port x VC12 & VC13 dbg", 0x3c)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port x VC10 & VC11 dbg", 0x3b)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port x VC8 & VC9 dbg", 0x3a)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port x VC6 & VC7 dbg", 0x39)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port x VC4 & VC5 dbg", 0x38)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port x VC2 & VC3 dbg", 0x37)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port x VC0 & VC1 dbg", 0x36)
            print()
            self.read_print_noc_reg(noc0_loc, noc_id, "router port y VC14 & VC15 dbg", 0x35)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port y VC12 & VC13 dbg", 0x34)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port y VC10 & VC11 dbg", 0x33)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port y VC8 & VC9 dbg", 0x32)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port y VC6 & VC7 dbg", 0x31)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port y VC4 & VC5 dbg", 0x30)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port y VC2 & VC3 dbg", 0x2f)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port y VC0 & VC1 dbg", 0x2e)
            print()
            self.read_print_noc_reg(noc0_loc, noc_id, "router port niu VC6 & VC7 dbg", 0x29)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port niu VC4 & VC5 dbg", 0x28)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port niu VC2 & VC3 dbg", 0x27)
            self.read_print_noc_reg(noc0_loc, noc_id, "router port niu VC0 & VC1 dbg", 0x26)

        en = 1
        rd_sel = 0
        pc_mask = 0x7fffffff
        daisy_sel = 7

        sig_sel = 0xff
        rd_sel = 0
        PCI_IFC.pci_write_xy(self.id(), *noc0_loc, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
        test_val1 = PCI_IFC.pci_read_xy(self.id(), *noc0_loc, 0, 0xffb1205c)
        rd_sel = 1
        PCI_IFC.pci_write_xy(self.id(), *noc0_loc, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
        test_val2 = PCI_IFC.pci_read_xy(self.id(), *noc0_loc, 0, 0xffb1205c)

        rd_sel = 0
        sig_sel = 2*self.SIG_SEL_CONST
        PCI_IFC.pci_write_xy(self.id(), *noc0_loc, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
        brisc_pc = PCI_IFC.pci_read_xy(self.id(), *noc0_loc, 0, 0xffb1205c) & pc_mask

        # Doesn't work - looks like a bug for selecting inputs > 31 in daisy stop
        # rd_sel = 0
        # sig_sel = 2*16
        # PCI_IFC.pci_write_xy(self.id(), *noc0_loc, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
        # nrisc_pc = PCI_IFC.pci_read_xy(self.id(), *noc0_loc, 0, 0xffb1205c) & pc_mask

        rd_sel = 0
        sig_sel = 2*10
        PCI_IFC.pci_write_xy(self.id(), *noc0_loc, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
        trisc0_pc = PCI_IFC.pci_read_xy(self.id(), *noc0_loc, 0, 0xffb1205c) & pc_mask

        rd_sel = 0
        sig_sel = 2*11
        PCI_IFC.pci_write_xy(self.id(), *noc0_loc, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
        trisc1_pc = PCI_IFC.pci_read_xy(self.id(), *noc0_loc, 0, 0xffb1205c) & pc_mask

        rd_sel = 0
        sig_sel = 2*12
        PCI_IFC.pci_write_xy(self.id(), *noc0_loc, 0, 0xffb12054, ((en << 29) | (rd_sel << 25) | (daisy_sel << 16) | (sig_sel << 0)))
        trisc2_pc = PCI_IFC.pci_read_xy(self.id(), *noc0_loc, 0, 0xffb1205c) & pc_mask

        print()
        x, y = noc0_loc
        print(f"Tensix x={x:02d},y={y:02d} => dbus_test_val1 (expect 7)={test_val1:x}, dbus_test_val2 (expect A5A5A5A5)={test_val2:x}")
        print(f"Tensix x={x:02d},y={y:02d} => brisc_pc=0x{brisc_pc:x}, trisc0_pc=0x{trisc0_pc:x}, trisc1_pc=0x{trisc1_pc:x}, trisc2_pc=0x{trisc2_pc:x}")

        PCI_IFC.pci_write_xy(self.id(), *noc0_loc, 0, 0xffb12054, 0)

    # Reads and immediately prints a value of a given NOC register
    def read_print_noc_reg(self, noc0_loc, noc_id, reg_name, reg_index):
        x, y = noc0_loc
        reg_addr = 0xffb20000 + (noc_id*0x10000) + 0x200 + (reg_index*4)
        val = PCI_IFC.pci_read_xy(self.id(), x, y, 0, reg_addr)
        print(f"Tensix x={x:02d},y={y:02d} => NOC{noc_id:d} {reg_name:s} = 0x{val:08x} ({val:d})")

    # Extracts and returns a single field of a stream register
    def get_stream_reg_field(self, noc0_loc, stream_id, reg_index, start_bit, num_bits):
        x, y = noc0_loc
        reg_addr = 0xFFB40000 + (stream_id*0x1000) + (reg_index*4)
        val = PCI_IFC.pci_read_xy(self.id(), x, y, 0, reg_addr)
        mask = (1 << num_bits) - 1
        val = (val >> start_bit) & mask
        return val

    def get_stream_phase (self, noc0_loc, stream_id):
        return self.get_stream_reg_field(noc0_loc, stream_id, 11, 0, 20)

    # Returns whether the stream is configured
    def is_stream_configured(self, stream_data):
        return int(stream_data['CURR_PHASE']) > 0

    def is_stream_idle(self, stream_data):
        return (stream_data["DEBUG_STATUS[7]"] & 0xfff) == 0xc00
    def is_stream_active (self, stream_data):
        return int (stream_data["CURR_PHASE"]) != 0 and int (stream_data["NUM_MSGS_RECEIVED"]) > 0
    def is_stream_done (self, stream_data):
        return int (stream_data["NUM_MSGS_RECEIVED"]) == int (stream_data["CURR_PHASE_NUM_MSGS_REMAINING"])
    def is_bad_stream (self, stream_data):
        return \
            (stream_data["DEBUG_STATUS[1]"] != 0) or \
            (stream_data["DEBUG_STATUS[2]"] & 0x7) == 0x4 or \
            (stream_data["DEBUG_STATUS[2]"] & 0x7) == 0x2
    def is_gsync_hung (self, noc0_loc):
        return PCI_IFC.pci_read_xy(self.id(), *noc0_loc, 0, 0xffb2010c) == 0xB0010000
    def is_ncrisc_done (self, noc0_loc):
        return PCI_IFC.pci_read_xy(self.id(), *noc0_loc, 0, 0xffb2010c) == 0x1FFFFFF1

    NCRISC_STATUS_REG_ADDR=0xFFB2010C
    BRISC_STATUS_REG_ADDR=0xFFB3010C

    def get_status_register_desc(self, register_address, reg_value_on_chip):
        STATUS_REG = {
            self.NCRISC_STATUS_REG_ADDR : [ #ncrisc
                { "reg_val":[0xA8300000,0xA8200000,0xA8100000], "description" : "Prologue queue header load",                                   "mask":0xFFFFF000, "ver": 0 },
                { "reg_val":[0x11111111],                       "description" : "Main loop begin",                                              "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xC0000000],                       "description" : "Load queue pointers",                                          "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xD0000000],                       "description" : "Which stream id will read queue",                              "mask":0xFFFFF000, "ver": 0 },
                { "reg_val":[0xD1000000],                       "description" : "Queue has data to read",                                       "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xD2000000],                       "description" : "Queue has l1 space",                                           "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xD3000000],                       "description" : "Queue read in progress",                                       "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xE0000000],                       "description" : "Which stream has data in l1 available to push",                "mask":0xFFFFF000, "ver": 0 },
                { "reg_val":[0xE1000000],                       "description" : "Push in progress",                                             "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xF0000000],                       "description" : "Which stream will write queue",                                "mask":0xFFFFF000, "ver": 0 },
                { "reg_val":[0xF0300000],                       "description" : "Waiting for stride to be ready before updating wr pointer",    "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xF1000000],                       "description" : "Needs to write data to dram",                                  "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xF2000000],                       "description" : "Ready to write data to dram",                                  "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xF3000000],                       "description" : "Has data to write to dram",                                    "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xF4000000],                       "description" : "Writing to dram",                                              "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0x20000000],                       "description" : "Amount of written tiles that needs to be cleared",             "mask":0xFFFFF000, "ver": 0 },
                { "reg_val":[0x22222222,0x33333333,0x44444444], "description" : "Epilogue",                                                     "mask":0xFFFFFFFF, "ver": 1 },
                { "reg_val":[0x10000006,0x10000001],            "description" : "Waiting for next epoch",                                       "mask":0xFFFFFFFF, "ver": 1 },
                { "reg_val":[0x1FFFFFF1],                       "description" : "Done",                                                         "mask":0xFFFFFFFF, "ver": 2 },
            ],
            self.BRISC_STATUS_REG_ADDR : [ #brisc
                { "reg_val":[0xB0000000],                       "description" : "Stream restart check",                                         "mask":0xFFFFF000, "ver": 0 },
                { "reg_val":[0xC0000000],                       "description" : "Check whether unpack stream has data",                         "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xD0000000],                       "description" : "Clear unpack stream",                                          "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xE0000000],                       "description" : "Check and push pack stream that has data (TM ops only)",       "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xF0000000],                       "description" : "Reset intermediate streams",                                   "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0xF1000000],                       "description" : "Wait until all streams are idle",                              "mask":0xFFFFFFFF, "ver": 0 },
                { "reg_val":[0x21000000],                       "description" : "Waiting for next epoch",                                       "mask":0xFFFFF000, "ver": 1 },
                { "reg_val":[0x10000001],                       "description" : "Waiting for next epoch",                                       "mask":0xFFFFFFFF, "ver": 1 },
                { "reg_val":[0x22000000],                       "description" : "Done",                                                         "mask":0xFFFFFF00, "ver": 2 },
            ]
        }

        if register_address in STATUS_REG:
            reg_value_desc_list = STATUS_REG[register_address]
            for reg_value_desc in reg_value_desc_list:
                mask = reg_value_desc["mask"]
                for reg_val_in_desc in reg_value_desc["reg_val"]:
                    if (reg_value_on_chip & mask == reg_val_in_desc):
                        return [reg_value_on_chip, reg_value_desc["description"], reg_value_desc["ver"]]
            return [reg_value_on_chip, "", 2]
        return []

    NCRISC_STATUS_REG_ADDR=NCRISC_STATUS_REG_ADDR
    BRISC_STATUS_REG_ADDR=BRISC_STATUS_REG_ADDR

    def read_stream_regs(self, noc0_loc, stream_id):
        return self.read_stream_regs_direct (noc0_loc, stream_id)

    def status_register_summary(self, addr, ver = 0):
        coords = self.get_block_locations ()
        status_descs = {}
        for loc in coords:
            status_descs[loc] = self.get_status_register_desc(addr, PCI_IFC.pci_read_xy(self.id(), loc[0], loc[1], 0, addr))

        # Print register status
        status_descs_rows = []
        for loc in coords:
            if status_descs[loc] and status_descs[loc][2] <= ver:
                status_descs_rows.append([f"{loc[0]:d}-{loc[1]:d}",f"{status_descs[loc][0]:08x}", f"{status_descs[loc][1]}"]);
        return status_descs_rows

    def as_noc_0 (self, noc_loc, noc_id):
        if noc_id == 0:
            return noc_loc
        else:
            return (self.noc1_to_noc0 (noc_loc))

    def stream_epoch (self, stream_regs):
        return int(stream_regs['CURR_PHASE']) >> 10

    def pci_read_xy(self, x, y, noc_id, reg_addr):
        return PCI_IFC.pci_read_xy(self.id(), x, y, noc_id, reg_addr)
    def pci_write_xy(self, x, y, noc_id, reg_addr, data):
        return PCI_IFC.pci_write_xy(self.id(), x, y, noc_id, reg_addr, data)
    def pci_read_tile(self, x, y, z, reg_addr, msg_size, data_format):
        return PCI_IFC.pci_read_tile(self.id(), x, y, z, reg_addr, msg_size, data_format)
