import os, subprocess, time, struct, signal
import zmq # For communication with Buda or debuda stub
import util

ZMQ_SOCKET=None

# Communication with Buda (or debuda-stub)
# See struct BUDA_READ_REQ
DEBUDA_STUB_PROCESS=None
def init_comm_client ():
    DEBUDA_STUB_PORT=5555

    print ("Spawning debuda-stub.")
    debuda_stub_path = util.application_path() + "/debuda-stub"
    try:
        global DEBUDA_STUB_PROCESS
        DEBUDA_STUB_PROCESS=subprocess.Popen([debuda_stub_path], preexec_fn=os.setsid)
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

def terminate_comm_client_callback ():
    os.killpg(os.getpgid(DEBUDA_STUB_PROCESS.pid), signal.SIGTERM)
    print (f"Terminated debuda-stub with pid:{DEBUDA_STUB_PROCESS.pid}")


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
