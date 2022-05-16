import os, subprocess, time, struct, signal, re, zmq
from tabulate import tabulate
import tt_util as util

#
# Communication with Buda (or debuda-stub) over sockets (ZMQ).
# See struct BUDA_READ_REQ for protocol details
#
ZMQ_SOCKET=None              # The socket for communication
DEBUDA_STUB_PROCESS_ID=None  # The process ID of debuda-stub spawned in init_comm_client

# Spawns debuda-stub and initializes the communication
def init_comm_client (debug_debuda_stub):
    DEBUDA_STUB_PORT=5555

    print ("Spawning debuda-stub.")
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

    #  Socket to talk to server
    print("Connecting to debuda-stub...")
    ZMQ_SOCKET = context.socket(zmq.REQ)
    ZMQ_SOCKET.connect(f"tcp://localhost:{DEBUDA_STUB_PORT}")
    print("Connected to debuda-stub.")

    ZMQ_SOCKET.send(struct.pack ("c", b'\x01')) # PING
    reply = ZMQ_SOCKET.recv_string()
    if "PONG" not in reply:
        print (f"Expected PONG but received {reply}") # Shoud print PONG

    time.sleep (0.1)

# Terminates debuda-stub spawned in init_comm_client
def terminate_comm_client_callback ():
    os.killpg(os.getpgid(DEBUDA_STUB_PROCESS_ID.pid), signal.SIGTERM)
    print (f"Terminated debuda-stub with pid:{DEBUDA_STUB_PROCESS_ID.pid}")

# PCI read/write functions. Given a noc0 location and addr, performs a PCI read/write
# to the given location at the address.
def pci_read_xy(chip_id, x, y, z, reg_addr):
    # print (f"Reading {x}-{y} 0x{reg_addr:x}")
    # ZMQ_SOCKET.send(struct.pack ("ccccci", b'\x02', chip_id, x, y, z, reg_addr))
    ZMQ_SOCKET.send(struct.pack ("cccccII", b'\x02', chip_id.to_bytes(1, byteorder='big'), x.to_bytes(1, byteorder='big'), y.to_bytes(1, byteorder='big'), z.to_bytes(1, byteorder='big'), reg_addr, 0))
    ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
    return ret_val
def pci_write_xy(chip_id, x, y, z, reg_addr, data):
    # print (f"Reading {x}-{y} 0x{reg_addr:x}")
    # ZMQ_SOCKET.send(struct.pack ("ccccci", b'\x02', chip_id, x, y, z, reg_addr))
    ZMQ_SOCKET.send(struct.pack ("cccccII", b'\x04', chip_id.to_bytes(1, byteorder='big'), x.to_bytes(1, byteorder='big'), y.to_bytes(1, byteorder='big'), z.to_bytes(1, byteorder='big'), reg_addr, data))
    ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
    assert data == ret_val
def host_dma_read (dram_addr):
    # print ("host_dma_read 0x%x" % dram_addr)
    ZMQ_SOCKET.send(struct.pack ("cccccI", b'\x03', b'\x00', b'\x00', b'\x00', b'\x00', dram_addr))
    ret_val = struct.unpack ("I", ZMQ_SOCKET.recv())[0]
    return ret_val

#
# Device class: generic constructs for talking to devices
#
class Device:
    # Class variable denoting the number of devices created
    num_devices = 0

    def create(arch):
        dev = None
        if arch == "grayskull":
            import tt_grayskull
            dev = tt_grayskull.GrayskullDevice()
        else:
            raise RuntimeError(f"Architecture {arch} not supported yet")

        dev._id = Device.num_devices
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

    def get_programmed_stream_locations(self, all_stream_regs):
        cores = set ()
        for loc, stream_regs in all_stream_regs.items():
            if self.is_stream_configured(stream_regs):
                cores.add (loc)
        return cores

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

    # Render and return a string
    def render (self, options="physical", emphasize_loc_list = set()):
        dev = self.yaml_file.root
        rows = []
        locs = dict()
        emphasize_loc_list_to_render = set()

        # Convert em\hasize_loc_list from noc0 coordinates to the coord space given by 'options' arg
        if options=="physical":
            for loc in emphasize_loc_list:
                emphasize_loc_list_to_render.add (self.noc_to_physical(loc, noc_id=0))
        else:
            emphasize_loc_list_to_render = emphasize_loc_list

        block_types = { 'functional_workers' : 'W', 'eth': 'E', 'arc' : 'A', 'dram' : 'D', 'pcie' : 'P', 'router_only' : '.' }

        # Convert the block locations to the coord space given by 'options' arg
        for block_name in block_types:
            for loc in self.get_block_locations (block_name):
                if options=="physical":
                    loc = self.noc_to_physical(loc, noc_id=0)
                locs[loc] = block_types[block_name]

        # Render the grid
        x_size = dev['grid']['x_size']
        y_size = dev['grid']['y_size']

        for y in range (y_size):
            row = []
            for x in range (x_size):
                render_str = ""
                if (x,y) in locs: render_str += locs[(x,y)]
                if (x,y) in emphasize_loc_list_to_render: render_str += "+"
                row.append (render_str)
            rows.append (row)

        return tabulate(rows, tablefmt='plain')

    def __str__(self):
        return self.render()
